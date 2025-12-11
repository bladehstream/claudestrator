---
name: Financial Application Domain Expert
id: financial_app
version: 1.0
category: domain
domain: [web, mobile, backend]
task_types: [design, implementation, feature]
keywords: [finance, budget, expense, transaction, money, currency, spending, income, account, bank, savings, investment, category, recurring, ledger, balance, payment]
complexity: [normal, complex]
pairs_with: [api_designer, database_designer, security_reviewer, data_visualization]
source: original
---

# Financial Application Domain Expert

## Role

You provide domain expertise for personal finance and budgeting applications. You understand transaction modeling, budget tracking, and the edge cases that cause bugs in financial software.

**Disclaimer**: This skill covers personal finance apps, NOT accounting-compliant, tax-preparation, or regulatory financial software.

## Core Competencies

- Transaction and account modeling
- Currency handling (avoiding float errors)
- Budget period calculations
- Recurring transaction patterns
- Transfer and refund handling
- Spending analysis and reporting

## Critical Rules

### NEVER Use Floats for Money
```javascript
// BAD - floating point errors
const total = 0.1 + 0.2; // 0.30000000000000004

// GOOD - store as integers (cents)
const total = 10 + 20; // 30 cents = $0.30

// Display: format at presentation layer
function formatCurrency(cents, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  }).format(cents / 100);
}
```

### Store Amounts as Integers
- Dollars: multiply by 100, store as cents
- High precision (crypto): multiply by 10^8 (satoshis)
- Use BIGINT for large amounts (>$21M needs more than 32-bit)

## Data Models

### Transaction
```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  amount_cents BIGINT NOT NULL,  -- Positive = income, Negative = expense
  currency CHAR(3) NOT NULL DEFAULT 'USD',

  -- Categorization
  category_id UUID REFERENCES categories(id),
  merchant VARCHAR(255),
  description TEXT,

  -- Metadata
  transaction_date DATE NOT NULL,  -- When it occurred
  posted_at TIMESTAMPTZ,           -- When it posted (NULL = pending)

  -- Relationships
  transfer_id UUID REFERENCES transfers(id),  -- Links transfer pairs
  parent_id UUID REFERENCES transactions(id), -- For split transactions

  -- Audit
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Account
```sql
CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(100) NOT NULL,
  account_type VARCHAR(20) NOT NULL,  -- checking, savings, credit, investment, cash
  currency CHAR(3) NOT NULL DEFAULT 'USD',

  -- Balance tracking
  current_balance_cents BIGINT NOT NULL DEFAULT 0,
  available_balance_cents BIGINT,  -- NULL if same as current

  -- Credit accounts
  credit_limit_cents BIGINT,  -- NULL for non-credit accounts

  -- External link
  institution_name VARCHAR(100),
  last_synced_at TIMESTAMPTZ,

  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Account types and their behaviors:
-- checking:   Normal debit, positive balance expected
-- savings:    Normal debit, positive balance expected
-- credit:     Negative balance = owed, positive = credit
-- investment: Can have negative (margin), track positions separately
-- cash:       Physical cash tracking
```

### Category Hierarchy
```sql
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),  -- NULL = system default
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(50) NOT NULL,
  icon VARCHAR(50),
  color CHAR(7),  -- Hex color

  -- Budgeting
  budget_cents BIGINT,
  budget_period VARCHAR(10),  -- monthly, weekly, yearly

  is_income BOOLEAN NOT NULL DEFAULT false,
  is_transfer BOOLEAN NOT NULL DEFAULT false,  -- For transfer category
  sort_order SMALLINT NOT NULL DEFAULT 0
);

-- Example hierarchy:
-- Food (parent)
--   ├── Groceries
--   ├── Restaurants
--   └── Coffee
-- Transportation (parent)
--   ├── Gas
--   ├── Public Transit
--   └── Rideshare
```

### Recurring Transaction Template
```sql
CREATE TABLE recurring_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),

  -- Transaction template
  amount_cents BIGINT NOT NULL,
  category_id UUID REFERENCES categories(id),
  merchant VARCHAR(255),
  description TEXT,

  -- Schedule
  frequency VARCHAR(20) NOT NULL,  -- daily, weekly, biweekly, monthly, yearly
  interval_count SMALLINT NOT NULL DEFAULT 1,  -- Every N periods
  day_of_week SMALLINT,  -- 0-6, for weekly
  day_of_month SMALLINT, -- 1-31, for monthly

  -- Bounds
  start_date DATE NOT NULL,
  end_date DATE,  -- NULL = indefinite

  -- Tracking
  last_generated_date DATE,
  next_occurrence DATE NOT NULL,

  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Business Logic Patterns

### Calculate Next Occurrence
```javascript
function getNextOccurrence(template, afterDate = new Date()) {
  const { frequency, interval_count, day_of_month, day_of_week, start_date } = template;

  let next = new Date(Math.max(afterDate, start_date));

  switch (frequency) {
    case 'monthly':
      // Handle month-end edge case
      next.setMonth(next.getMonth() + interval_count);
      const targetDay = Math.min(day_of_month, daysInMonth(next));
      next.setDate(targetDay);
      break;

    case 'weekly':
      const daysUntil = (day_of_week - next.getDay() + 7) % 7 || 7;
      next.setDate(next.getDate() + daysUntil);
      break;

    // ... other frequencies
  }

  return next;
}

// Edge case: Jan 31 + 1 month = Feb 28/29, NOT Mar 3
function daysInMonth(date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
}
```

### Handle Transfers
```javascript
// A transfer creates TWO transactions linked by transfer_id
async function createTransfer(fromAccountId, toAccountId, amountCents, date) {
  const transferId = uuid();

  // Outflow from source
  const outflow = await createTransaction({
    account_id: fromAccountId,
    amount_cents: -amountCents,  // Negative = outflow
    transfer_id: transferId,
    category_id: TRANSFER_CATEGORY_ID,
    description: `Transfer to ${toAccountName}`
  });

  // Inflow to destination
  const inflow = await createTransaction({
    account_id: toAccountId,
    amount_cents: amountCents,  // Positive = inflow
    transfer_id: transferId,
    category_id: TRANSFER_CATEGORY_ID,
    description: `Transfer from ${fromAccountName}`
  });

  return { transferId, outflow, inflow };
}

// CRITICAL: Exclude transfers from spending reports
// They're not expenses, just money movement
```

### Handle Refunds
```javascript
// Option 1: Negative expense (simple)
const refund = {
  amount_cents: 2500,  // Positive, but in expense category
  category_id: originalTransaction.category_id,
  description: 'Refund: Original purchase'
};

// Option 2: Link to original (better tracking)
const refund = {
  amount_cents: 2500,
  category_id: originalTransaction.category_id,
  refund_for_id: originalTransaction.id  // Custom field
};

// In reports: net spend = expenses + refunds in same category
```

### Credit Card Payment Edge Case
```javascript
// Credit card payment should NOT show as expense
// It's a transfer from checking to credit card

// BAD: Creates duplicate "spending"
// - Original purchase: -$100 (expense) ✓
// - Payment to CC: -$100 (expense) ✗ DOUBLE COUNTED!

// GOOD: Mark as transfer
// - Original purchase: -$100 (expense) ✓
// - Payment: Transfer from checking to credit ✓
```

## Date Handling

### Timezone Rules
```javascript
// Store transaction_date as DATE (no time component)
// Store timestamps as TIMESTAMPTZ (with timezone)

// Display in user's local timezone
const displayDate = new Intl.DateTimeFormat('en-US', {
  timeZone: userTimezone
}).format(transaction.posted_at);

// Date range queries: use start of day in user's timezone
function getDateRange(userTimezone, year, month) {
  const startLocal = new Date(year, month - 1, 1);
  const endLocal = new Date(year, month, 0, 23, 59, 59);

  // Convert to UTC for database query
  return {
    start: zonedTimeToUtc(startLocal, userTimezone),
    end: zonedTimeToUtc(endLocal, userTimezone)
  };
}
```

### Period Boundaries
```sql
-- Monthly report: inclusive on both ends
WHERE transaction_date >= '2024-01-01'
  AND transaction_date <= '2024-01-31'

-- Or use range operator
WHERE transaction_date BETWEEN '2024-01-01' AND '2024-01-31'
```

## UI/UX Patterns

### Amount Input
```jsx
function CurrencyInput({ value, onChange }) {
  const [display, setDisplay] = useState(formatCurrency(value));

  const handleChange = (e) => {
    // Strip non-numeric, parse to cents
    const raw = e.target.value.replace(/[^0-9.-]/g, '');
    const cents = Math.round(parseFloat(raw) * 100) || 0;
    onChange(cents);
    setDisplay(formatCurrency(cents));
  };

  return (
    <input
      type="text"
      inputMode="decimal"  // Mobile: numeric keyboard with decimal
      value={display}
      onChange={handleChange}
      onBlur={() => setDisplay(formatCurrency(value))}
    />
  );
}
```

### Quick Entry Pattern
- Default date to today
- Remember last-used category per merchant
- Auto-suggest merchant from history
- Tab order: Amount → Merchant → Category → Date → Save

### Running Balance
```sql
-- Calculate running balance for statement view
SELECT
  t.*,
  SUM(amount_cents) OVER (
    PARTITION BY account_id
    ORDER BY transaction_date, created_at
    ROWS UNBOUNDED PRECEDING
  ) as running_balance_cents
FROM transactions t
WHERE account_id = ?
ORDER BY transaction_date DESC, created_at DESC;
```

## Reporting Queries

### Spending by Category
```sql
SELECT
  c.name as category,
  c.parent_id,
  SUM(ABS(t.amount_cents)) as total_cents,
  COUNT(*) as transaction_count
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.account_id = ANY(?)
  AND t.amount_cents < 0  -- Expenses only
  AND c.is_transfer = false  -- Exclude transfers
  AND t.transaction_date BETWEEN ? AND ?
GROUP BY c.id, c.name, c.parent_id
ORDER BY total_cents DESC;
```

### Budget vs Actual
```sql
SELECT
  c.id,
  c.name,
  c.budget_cents,
  COALESCE(SUM(ABS(t.amount_cents)), 0) as spent_cents,
  c.budget_cents - COALESCE(SUM(ABS(t.amount_cents)), 0) as remaining_cents
FROM categories c
LEFT JOIN transactions t ON t.category_id = c.id
  AND t.amount_cents < 0
  AND t.transaction_date BETWEEN ? AND ?
WHERE c.user_id = ?
  AND c.budget_cents IS NOT NULL
GROUP BY c.id;
```

## Export Formats

### CSV Export
```javascript
const headers = ['Date', 'Merchant', 'Category', 'Amount', 'Account'];
const rows = transactions.map(t => [
  t.transaction_date,
  t.merchant,
  t.category_name,
  (t.amount_cents / 100).toFixed(2),
  t.account_name
]);
```

### OFX (for bank import)
```xml
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20240115</DTPOSTED>
            <TRNAMT>-45.00</TRNAMT>
            <NAME>GROCERY STORE</NAME>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
```

## Common Gotchas

| Gotcha | Problem | Solution |
|--------|---------|----------|
| Float arithmetic | $0.10 + $0.20 ≠ $0.30 | Store as integer cents |
| Jan 31 + 1 month | Feb 31 doesn't exist | Clamp to month end |
| Credit card payments | Double-counted as spending | Mark as transfer |
| Transfers in reports | Inflates spending totals | Exclude transfer category |
| Pending transactions | Balance confusion | Show separate pending total |
| Timezone boundaries | Wrong day for transactions | Store dates without time |
| Split transactions | Category totals incorrect | Sum child transactions |

## Output Expectations

When this skill is applied, the agent should:

- [ ] Store money as integers (cents)
- [ ] Handle transfers as linked pairs
- [ ] Exclude transfers from spending reports
- [ ] Handle recurring transaction edge cases
- [ ] Use proper date range queries
- [ ] Consider credit vs debit account behaviors
- [ ] Provide clear running balance calculations

---

*Skill Version: 1.0*

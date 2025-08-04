# Work with Information: Defining Variables

## Getting Started

When you need to save information in your program, you'll **Define** variables specifying its type
and default values.

**WAIT!** Let me tell what it means in a human-friendly way.

### What's a variable?

Think of it like a labeled box where you store information. Just like you might have a box labeled
"receipts" to hold your receipts, a variable has a name and holds a value that can change. For
example, `people inside` might be a variable that holds the number of people inside a store. It can
be `5` now but `8` later.

### Variable Types

Variables has types, depending on the type of information it can save. It could be:

- **status** - For yes/no questions (like "Is the door open?")
- **whole number** - For counting things (like 5 people, 10 items)
- **decimal** - For precise numbers with decimal points (like a price: 19.99)
- **number** - For any number, whole or decimal
- **text** - For words and sentences (like names or addresses)
- **link** - For web addresses (like <https://example.com>)

### Descriptions

### Default Values

## How to Define Variables

Use this format:

```markdown
**Define** `variable name` **as** a **type**.
_Description of what it's for_ (**default**: _value_).
```

## Examples

### Status

```markdown
**Define** `alarm is on` **as** a **status**.
_Whether the store's alarm is turned on_ (**default**: _Yes_).
```

```markdown
**Define** `door is open` **as** a **status**.
_Whether the store's door is currently open_ (**default**: _No_).
```

### Numbers

```markdown
**Define** `people inside` **as** a **whole number**.
_How many people are in the store_ (**default**: _0_).
```

```markdown
**Define** `temperature` **as** a **decimal**.
_The temperature in degrees_ (**default**: _72.5_).
```

### Texts

```markdown
**Define** `name` **as** **text**.
_The name of the store_ (**default**: _"My Store"_).
```

### Links

```markdown
**Define** `website` **as** a **link**.
_Link to the store's website_ (**default**: _"https://mystore.com"_).
```

## Writing Good Descriptions

### For **status** (yes/no)

Start with "Whether..."

- ✓ _Whether the alarm is active_
- ✗ _Variable to store alarm state_

### For **whole number** (counting)

Start with "How many..." or "The number of..."

- ✓ _How many items in cart_
- ✗ _Cart items count variable_

### For **decimal** (precise numbers)

Start with "The amount of..." or specify units

- ✓ _The price in dollars_
- ✗ _Price variable_

### For **number** (any number)

Start with "The..."

- ✓ _The amount of points granted to the customer on each purchase_
- ✗ _User's points_

### For **text** (words)

Start with "The..." or "Any..."

- ✓ _The customer's name_
- ✗ _Name string variable_

### For **link** (web addresses)

Start with "Link to..." or "Web address for..."

- ✓ _Link to the help page_
- ✗ _Help URL variable_

## Possible Values

- **status**: `Yes` or `No`
- **whole number**: `0`, `1`, `2`, `100`, etc. (no decimals!)
- **decimal**: `0.5`, `19.99`, `98.6`, `101.0`, etc.
- **number**: Any number, whole or decimal
- **text**: Any words in quotes like `"Hello, World!"`
- **link**: Web addresses in quotes like `"https://example.com"`

## Tips

1. Keep variable names simple and clear
1. Prefer long descriptions only if you can't be precise with a few words
1. Always include a description - your future self will thank you!
1. Set sensible defaults (it's mandatory)
1. Use **whole number** when decimals don't make sense (can't have 2.5 people!)
1. Use **decimal** when precision matters (prices, measurements)
1. Use **number** when you want flexibility

That's it! You're ready to start defining variables in a way everyone can understand. 🎉

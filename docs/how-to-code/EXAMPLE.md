---
executable: true
---

# Store's Alarm System

## Traits

**Define** `alarm is on` **as** a **status**.\
_Whether the store's alarm is turned on_ (**default**: _Yes_).

**Define** `door is open` **as** a **status**.\
_Whether the store's door is currently open_ (**default**: _No_).

**Define** `people inside` **as** a **whole number**.\
_How many people are in the store_ (**default**: _0_).

## Behaviors

### **Action**: `make noise`

<details>
<summary>Emits the sound of the alarm.</summary>

> Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.\
> **Say** `noise`.

</details>

#### Inputs

- `sound` **as** Text (required)
- `volume` **as** Whole Number (optional, default: 60)

#### Outputs

- `success` **as** Status

### **Interaction**: `turn alarm off`

<details>
<summary>Turns off the alarm when it is on.</summary>

> **if** `alarm is on` **then**:
>
> > **Set** `alarm is on` **to** _No_.\
> > **Say** _"Alarm has been turned off"_

</details>

## Rule

### 1. Alarm makes noise when security is violated

**if** `alarm is on` **and** **either** `people inside` **is at least** _1_ **or** `door is open`
**then**, **trigger** `make noise`.

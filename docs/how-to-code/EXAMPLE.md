---
executable: true
---

# Store's Alarm System

## Traits

**Define** `alarm is on` **as** a **status**.
_Whether the store's alarm is turned on_ (**default**: _Yes_).

**Define** `door is open` **as** a **status**.
_Whether the store's door is currently open_ (**default**: _No_).

**Define** `people inside` **as** a **whole number**.
_How many people are in the store_ (**default**: _0_).

## Actions

### **Define interaction called**  `toggle alarm status`

Turns on the alarm when it is off and turn it off if it is on.

### Instructions

> **if** `alarm is on` **then**:
>
> > **Set** `alarm is on` **to** _No_.
> > **Print** _"Alarm has been turned off"_
>
> **otherwise:**
>
> > **Set** `alarm is on` **to** _Yes_.
> > **Print** _"Alarm has been turned on"_

### **Define behaviour `make noise`**

> Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.
> **Print** `noise`.

## Rule

### 1. Alarm makes noise when security is violated

**if** `alarm is on` **and** **either** `people inside` **is at least** _1_ **or** `door is open`
**then**, **trigger** `make noise`.

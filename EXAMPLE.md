# Store's Alarm System

## Traits

**Set** `store door status` **to** `unlocked`.
**Set** `store alarm status` **to** `on`.
**Set** `people inside` **to** `3`.

## Actions

### **Define** `activate alarm`

**Apply** `make noise` **with** `volume` = _100_.
**Apply** `flash lights` **with** `intensity` = _"max"_.
**Apply** `notify security`.

## Rule

**If** `store door status` **is not** the **same as** `store alarm status` **and** `people inside`
**is more than** _0_, **then apply** `activate alarm`.

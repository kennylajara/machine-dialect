# Fibonacci Calculator

This program calculates the nth Fibonacci number using recursion.

## **Interaction**: `fibonacci`

Calculate the nth Fibonacci number.

### Input

- `n` (Whole Number): The position in the Fibonacci sequence

### Output

- Gives back a Whole Number

<details>
<summary>Calculate Fibonacci number recursively</summary>

> If `n` is less than or equal to _1_:
>
> > Give back `n`.
>
> Otherwise:
>
> > Define `n_minus_1` as Whole Number.\
> > Set `n_minus_1` to `n` minus _1_.\
> > Define `n_minus_2` as Whole Number.\
> > Set `n_minus_2` to `n` minus _2_.\
> > Define `fib_1` as Whole Number.\
> > Call `fibonacci` with `n_minus_1` and store in `fib_1`.\
> > Define `fib_2` as Whole Number.\
> > Call `fibonacci` with `n_minus_2` and store in `fib_2`.\
> > Define `result` as Whole Number.\
> > Set `result` to `fib_1` plus `fib_2`.\
> > Give back `result`.

</details>

## Main Program

<details>
<summary>Calculate Fibonacci(40) for benchmark.</summary>

> Define `n` as Whole Number.\
> Set `n` to _40_.
>
> Define `result` as Whole Number.\
> Call `fibonacci` with `n` and store in `result`.
>
> Say _"Fibonacci of 40 is:"_.\
> Say `result`.

</details>

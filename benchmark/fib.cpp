#include <iostream>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { std::cout << fib(40) << std::endl; return 0; }

#!/usr/bin/env python3
"""
Standalone benchmark runner for local testing without Docker.
This allows testing Machine Dialect performance directly.
"""

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

ITERATIONS = 5
FIBONACCI_N = 30
EXPECTED_RESULT = 832040


def run_command(cmd: list[str], timeout: int = 120) -> tuple[str, float]:
    """Run a command and return output and execution time."""
    start = time.perf_counter()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        end = time.perf_counter()
        return result.stdout.strip(), (end - start) * 1000  # Convert to ms
    except subprocess.TimeoutExpired:
        return "TIMEOUT", timeout * 1000
    except Exception as e:
        return f"ERROR: {e}", -1


def compile_programs() -> dict[str, dict[str, Any]]:
    """Compile all test programs and return command configurations."""
    programs = {}

    # C Implementation
    c_code = """#include <stdio.h>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { printf("%d\\n", fib(30)); return 0; }
"""
    with open("fib.c", "w") as f:
        f.write(c_code)
    if (
        subprocess.run(
            ["gcc", "-O3", "-march=native", "-mtune=native", "-flto", "fib.c", "-o", "fib_c"], capture_output=True
        ).returncode
        == 0
    ):
        programs["C"] = {"cmd": ["./fib_c"], "mode": "compiled"}

    # C++ Implementation
    cpp_code = """#include <iostream>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { std::cout << fib(30) << std::endl; return 0; }
"""
    with open("fib.cpp", "w") as f:
        f.write(cpp_code)
    if (
        subprocess.run(
            ["g++", "-O3", "-march=native", "-mtune=native", "-flto", "fib.cpp", "-o", "fib_cpp"], capture_output=True
        ).returncode
        == 0
    ):
        programs["C++"] = {"cmd": ["./fib_cpp"], "mode": "compiled"}

    # Go Implementation
    if shutil.which("go"):
        go_code = """package main
import "fmt"
func fib(n int) int {
    if n <= 1 { return n }
    return fib(n-1) + fib(n-2)
}
func main() { fmt.Println(fib(30)) }
"""
        with open("fib.go", "w") as f:
            f.write(go_code)
        if (
            subprocess.run(
                ["go", "build", "-ldflags", "-s -w", "-o", "fib_go", "fib.go"], capture_output=True
            ).returncode
            == 0
        ):
            programs["Go"] = {"cmd": ["./fib_go"], "mode": "compiled"}

    # Rust Implementation
    if shutil.which("rustc"):
        rust_code = """fn fib(n: i32) -> i32 {
    if n <= 1 { n } else { fib(n-1) + fib(n-2) }
}
fn main() { println!("{}", fib(30)); }
"""
        with open("fib.rs", "w") as f:
            f.write(rust_code)
        if (
            subprocess.run(
                ["rustc", "-C", "opt-level=3", "-C", "target-cpu=native", "-C", "lto=fat", "fib.rs", "-o", "fib_rust"],
                capture_output=True,
            ).returncode
            == 0
        ):
            programs["Rust"] = {"cmd": ["./fib_rust"], "mode": "compiled"}

    # Java Implementation
    if shutil.which("javac") and shutil.which("java"):
        java_code = """public class Fib {
    static int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
    public static void main(String[] args) { System.out.println(fib(30)); }
}
"""
        with open("Fib.java", "w") as f:
            f.write(java_code)
        if subprocess.run(["javac", "Fib.java"], capture_output=True).returncode == 0:
            programs["Java"] = {"cmd": ["java", "Fib"], "mode": "jit"}

    # JavaScript Implementation
    if shutil.which("node"):
        js_code = """function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
console.log(fib(30));
"""
        with open("fib.js", "w") as f:
            f.write(js_code)
        programs["JavaScript"] = {"cmd": ["node", "fib.js"], "mode": "jit"}

    # Python Implementation
    py_code = """def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)
print(fib(30))
"""
    with open("fib.py", "w") as f:
        f.write(py_code)
    programs["Python"] = {"cmd": ["python3", "fib.py"], "mode": "interpreted"}

    # Ruby Implementation
    if shutil.which("ruby"):
        ruby_code = """def fib(n); n <= 1 ? n : fib(n-1) + fib(n-2); end
puts fib(30)
"""
        with open("fib.rb", "w") as f:
            f.write(ruby_code)
        programs["Ruby"] = {"cmd": ["ruby", "fib.rb"], "mode": "interpreted"}

    # Perl Implementation
    if shutil.which("perl"):
        perl_code = """sub fib { my $n = shift; $n <= 1 ? $n : fib($n-1) + fib($n-2) }
print fib(30), "\\n";
"""
        with open("fib.pl", "w") as f:
            f.write(perl_code)
        programs["Perl"] = {"cmd": ["perl", "fib.pl"], "mode": "interpreted"}

    # C# Implementation
    if shutil.which("dotnet"):
        csharp_code = """using System;
class Program {
    static int Fib(int n) => n <= 1 ? n : Fib(n-1) + Fib(n-2);
    static void Main() => Console.WriteLine(Fib(30));
}
"""
        # Create a temporary directory for C# project
        import os
        import tempfile

        csharp_dir = tempfile.mkdtemp(prefix="csharp_bench_")

        # Write the C# code
        with open(os.path.join(csharp_dir, "Program.cs"), "w") as f:
            f.write(csharp_code)

        # Create project file
        csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <PublishAot>true</PublishAot>
    <OptimizationPreference>Speed</OptimizationPreference>
    <Optimize>true</Optimize>
  </PropertyGroup>
</Project>
"""
        with open(os.path.join(csharp_dir, "FibBench.csproj"), "w") as f:
            f.write(csproj_content)

        # Build the project with release configuration
        if (
            subprocess.run(
                ["dotnet", "build", "-c", "Release", "--nologo", "-v", "q"], cwd=csharp_dir, capture_output=True
            ).returncode
            == 0
        ):
            programs["C#"] = {
                "cmd": ["dotnet", "run", "-c", "Release", "--no-build", "--project", csharp_dir],
                "mode": "jit",
            }

    # Machine Dialect Implementation
    if Path("fib.md").exists():
        # First compile the Machine Dialect code
        compile_result = subprocess.run(
            ["python3", "-m", "machine_dialect", "compile", "fib.md", "-o", "fib.mdb", "--opt-level", "3"],
            capture_output=True,
            text=True,
        )
        if compile_result.returncode == 0:
            programs["Machine Dialect (Compiled)"] = {
                "cmd": ["python3", "-m", "machine_dialect", "run", "fib.mdb"],
                "mode": "bytecode",
            }
        else:
            print(f"Machine Dialect compilation failed: {compile_result.stderr}")

    return programs


def run_benchmark(name: str, config: dict[str, Any]) -> dict[str, Any]:
    """Run benchmark for a single language."""
    print(f"Testing {name} ({config['mode']})...")

    cmd = config["cmd"]
    mode = config["mode"]

    # Warm-up for JIT languages
    if mode == "jit":
        for _ in range(3):
            run_command(cmd, timeout=60)

    # Measure execution times
    times = []
    valid = True
    for _ in range(ITERATIONS):
        output, duration = run_command(cmd)
        times.append(duration)

        # Validate output
        if output != str(EXPECTED_RESULT):
            print(f"  WARNING: {name} produced output: {output} (expected: {EXPECTED_RESULT})")
            valid = False

    # Calculate statistics
    times_sorted = sorted(times)
    return {
        "language": name,
        "mode": mode,
        "times_ms": times,
        "min_ms": times_sorted[0],
        "max_ms": times_sorted[-1],
        "median_ms": times_sorted[len(times_sorted) // 2],
        "valid": valid,
    }


def main() -> None:
    """Main benchmark runner."""
    print("=" * 60)
    print("Machine Dialect Performance Benchmark")
    print("=" * 60)
    print(f"Fibonacci({FIBONACCI_N}) - {ITERATIONS} iterations per language\n")

    # Compile all programs
    print("Compiling programs...")
    programs = compile_programs()
    print(f"Found {len(programs)} languages to test\n")

    # Run benchmarks
    results = []
    for name, config in programs.items():
        try:
            result = run_benchmark(name, config)
            results.append(result)
        except Exception as e:
            print(f"  ERROR running {name}: {e}")

    # Sort by median time
    results.sort(key=lambda x: x["median_ms"])

    # Save results
    output = {"benchmark": "fibonacci", "n": FIBONACCI_N, "iterations": ITERATIONS, "results": results}

    with open("benchmark_results.json", "w") as f:
        json.dump(output, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS - Fibonacci(30)")
    print("=" * 60)
    print(f"{'Rank':<5} {'Language':<30} {'Median (ms)':<12} {'Mode':<12}")
    print("-" * 60)

    for i, r in enumerate(results, 1):
        valid_mark = "" if r.get("valid", True) else " (!)"
        print(f"{i:<5} {r['language'] + valid_mark:<30} {r['median_ms']:<12.1f} {r['mode']:<12}")

    print("=" * 60)
    if results:
        print(f"Fastest: {results[0]['language']} ({results[0]['median_ms']:.1f}ms)")
        print(f"Slowest: {results[-1]['language']} ({results[-1]['median_ms']:.1f}ms)")
        if results[0]["median_ms"] > 0:
            print(f"Speedup: {results[-1]['median_ms'] / results[0]['median_ms']:.1f}x")

    print("\nResults saved to benchmark_results.json")

    # Clean up
    for file in Path(".").glob("fib.*"):
        file.unlink()
    for file in Path(".").glob("Fib.*"):
        file.unlink()
    for file in Path(".").glob("*.class"):
        file.unlink()
    for file_str in ["fib_c", "fib_cpp", "fib_go", "fib_rust"]:
        file = Path(file_str)
        if file.exists():
            file.unlink()

    # Clean up C# temporary directories
    import shutil
    import tempfile

    temp_dir = Path(tempfile.gettempdir())
    for csharp_dir in temp_dir.glob("csharp_bench_*"):
        if csharp_dir.is_dir():
            shutil.rmtree(csharp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

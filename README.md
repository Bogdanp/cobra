# Cobra

Reads in a subset of C source code and interprets it using the CPython
VM. Why? For the lulz.

# Usage

    cobra FILENAME

# Example

Save the following to `euclid.c`:

    int gcd(int a, int b) {
        while (a != b) {
            if (a > b) a -= b;
            else       b -= a;
        }

        return a;
    }

    void main() {
        print(gcd(48, 36));
    }

And then run it:

    $ cobra euclid.c
    12

# TODOs

* Make assignment act like an expression.
* Add a type checker.

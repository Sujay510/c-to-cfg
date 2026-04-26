#include <stdio.h>

int foo(int x) {
    return x + 1;
}

int main() {
    int a = 5;
    int b = a + 2;
    

    if (b > 5) {
        b = foo(b);
    } else {
        b = b - 1;
    }

    for (int i = 0; i < 3; i++) {
        b = b + i;
    }

    while (a < 10) {
        a = a + 1;
        if (a == 7) continue;
        if (a == 9) break;
        b = b + a;
    }
  a=6;
    return b;
}
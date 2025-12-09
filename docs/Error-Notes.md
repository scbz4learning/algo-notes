# 错题笔记

## C++ Syntax 

### Sort  
```cpp
sort (
    nums.begin(),
    nums.end(),
    [&](int x, int y) {
        return toIndex(x) == toIndex(y)
            ? x < y
            : toIndex(x) < toIndex(y);
    }
);
```

## Math 

### 质数
1. Naive 算法判断质数 3 个问题:
    1. `for` 从 2 开始  
    2. `for` 的循环终止条件 `i * i <= x` 必须要 `<=`, 不然 `9 % 3 = 0` 但是 `3 * 3 < 9` 为假, 所以被提前跳过了.  
    3.  `if (!(x % i))` 没有余数 -> 整除 -> 不是质数 -> 返回 false  
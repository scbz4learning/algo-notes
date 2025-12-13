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

List:

+ [3769](./LeetCode/3769.md)

### `find`
从 c++11 开始, 如果找不到元素:

* `std::find(It start, It end, value)` 返回的是 `end()` 迭代器。
* `str.find(value)` (`str` 是一个 `std::string` 类型的实例) 返回的是 `std::string::npos` 常量。

List:

+ [0345](./LeetCode/0345.md)

### 

## Math 

### GCD 

欧几里得算法:  

$$
\text{gcd}(a, b) = \text{gcd}(b, a \bmod b)
$$
  

1. **第一次计算**:
    * `a = 56`, `b = 98`  
    * 计算 `98 % 56 = 42`  
    * 因此 `gcd(56, 98) = gcd(98, 42)`  
2. **第二次计算**：
    * `a = 98`, `b = 42`
    * 计算 `98 % 42 = 14`
    * 因此 `gcd(98, 42) = gcd(42, 14)`
3. **第三次计算**：
    * `a = 42`, `b = 14`
    * 计算 `42 % 14 = 0`
    * 因此 `gcd(42, 14) = 14`

时间复杂度：$O(\log(\min(a, b)))$。这是因为每次递归都会使较大的数变得越来越小，直到某一方为零。

List:

+ [1071](./LeetCode/1071.md)

### 质数
1. Naive 算法判断质数 3 个问题:
    1. `for` 从 2 开始  
    2. `for` 的循环终止条件 `i * i <= x` 必须要 `<=`, 不然 `9 % 3 = 0` 但是 `3 * 3 < 9` 为假, 所以被提前跳过了.  
    3.  `if (!(x % i))` 没有余数 -> 整除 -> 不是质数 -> 返回 false 


List: 

+ [3770](./LeetCode/3770.md) 
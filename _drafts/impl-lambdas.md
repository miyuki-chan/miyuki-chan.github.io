---
layout: post
comments: true
title: 'Implementation of the C++ lambdas'
tags:
  - 'C++'
---
The C++11 standard included lots of new features  probably one the most widely
used of them today is lambda expressions.

...

Consider the following example:

{% highlight C++ %}
```
#include <iostream>
#include <string_view>

int main() {
    std::string_view greeting = "Hello";
    auto hello = [&](std::string_view name) {
        std::cout << greeting << ", " << name << ".\n";
    };
    hello("world");
}
```
{% endhighlight %}

As you might recognize, this is just a fancy way of printing "Hello, world." to
stdout. Function `main` defines a lambda and assigns is to variable `hello` and
immediately invokes it. To be more precise, what we assign to `hello` is the
result of the following expression:

`[&](std::string_view name) { std::cout << greeting << ", " << name << ".\n"; }`

Such an expression is called a *lambda-expression*, and its result (the value
of `hello`) is called the *closure object*.

What type does the variable `hello` have? The standard says that it's called
(unsurprisingly) the *closure type*. \[expr.prim.lambda\] also mentions that
it is a unique, unnamed non-union class type.

Let's compile this program with GCC and run it under the debugger. We will set
a breakpoint on `main` and then print the type of `hello`:

```
(gdb) break main
Breakpoint 1 at 0x40089f: file test.cpp, line 6.
(gdb) run
Starting program: /home/miyuki/projects/temp/a.out

Breakpoint 1, main () at test.cpp:6
6           std::string_view greeting = "Hello";
(gdb) ptype hello
type = struct <lambda(std::string_view)> {
    std::string_view &__greeting;
}
```

As we can see, the closure is just a `struct` with a single member called
`__greeting`. Now let's set a breakpoint inside the lambda and continue
the program execution:

```
(gdb) break 7
Breakpoint 2 at 0x400843: file test.cpp, line 7.
(gdb) continue
Continuing.

Breakpoint 2, <lambda(std::string_view)>::operator()(std::string_view) const (__closure=0x7fffffffe470, name=...)
    at test.cpp:8
8               std::cout << greeting << ", " << name << ".\n";
(gdb) backtrace
#0  <lambda(std::string_view)>::operator()(std::string_view) const (__closure=0x7fffffffe470, name=...) at test.cpp:8
#1  0x00000000004008e0 in main () at test.cpp:10
```

Execution stopped inside the function called
`<lambda(std::string_view)>::operator()(std::string_view)`. The signature
of this function is perfectly in according to the description in the
C++ standard:

> The closure type for a non-generic *lambda-expression* has a public inline
> function call operator whose parameters and return type are described by the
> lambda-expression’s *parameter-declaration-clause* and *trailing-return-type*
> respectively

Note that this function has two parameters: `__closure` and `name`. The second
one was provided by us, and the first one was added by the compiler: it is the
address of the closure object. Actually, it's pretty similar to the way the
`this` pointer is passed to class methods.

If we go one frame up and print the address of variable `hello`, we will see,
that it matches the address passed as `__closure` to the function call operator:

```
(gdb) up
#1  0x00000000004008e0 in main () at test.cpp:10
10          hello("world");
(gdb) print &hello
$2 = (<lambda(std::string_view)> *) 0x7fffffffe470
```

Now we can rewrite the example like this:

{% highlight C++ %}
```
#include <iostream>
#include <string_view>

int main() {
    struct hello_t {
        hello_t(std::string_view& greeting) : __greeting(greeting) { }
        inline void operator()(std::string_view name) const {
            std::cout << __greeting << ", " << name << ".\n";
        }
        std::string_view& __greeting;
    };
    std::string_view greeting = "Hello";
    auto hello = hello_t(greeting);
    hello("world");
}
```
{% endhighlight %}

The lambda is now replaced with a plain old function object, but the generated
code is almost equivalent to that of the previous example.

If we capture several values, it is up to the compiler to decide how they are
laid out in memory. This layout is intentionally not specified by the standard
and even by the ABI. The reason for this omission in the ABI is that lambdas are
always local to the translation unit they are defined in: the only code that
interacts with this layout is the function that initializes the closure object
and the function call operator of the closure type. This is actually good news,
because the future version of GCC can leverage the freedom to change the layout
to implement optimizations without breaking binary compatibility with the
existing code.

By the way, a common misconception associated with lambdas is that they require
heap memory allocation. As you can see this is not true: the closure object
is allocated on the stack.

## Converting lambdas into function pointers

Another interesting feature of lambdas is that lambdas that don't capture any
values can be converted to plain function pointers. Let's find out how
this works. Consider another example:

{% highlight C++ %}
```
#include <iostream>
#include <string_view>

using fnptr_t = void(*)(std::string_view);

void test(fnptr_t fn) {
    fn("world");
}

int main() {
    auto hello = [](std::string_view name) {
        std::cout << "Hello, " << name << ".\n";
    };
    test(hello);
}
```
{% endhighlight %}

Again, we start the program under the debugger and set a breakpoint inside the
lambda:

```
(gdb) break 14
Breakpoint 1 at 0x400877: file test2.cpp, line 14.
(gdb) run
Starting program: /home/miyuki/projects/temp/a.out

Breakpoint 1, <lambda(std::string_view)>::operator()(std::string_view) const (__closure=0x0, name=...) at test2.cpp:14
14              std::cout << "Hello, " << name << ".\n";
(gdb) backtrace
#0  <lambda(std::string_view)>::operator()(std::string_view) const (__closure=0x0, name=...) at test2.cpp:14
#1  0x00000000004008e0 in <lambda(std::string_view)>::_FUN(std::string_view) () at test2.cpp:15
#2  0x0000000000400857 in test (fn=0x4008af <<lambda(std::string_view)>::_FUN(std::string_view)>) at test2.cpp:8
#3  0x000000000040090d in main () at test2.cpp:16
```

The backtrace is somewhat interesting: the actual value passed to function `test`
is displayed as `<lambda(std::string_view)>::_FUN`. `_FUN` is of course a
compiler-generated name specific to GCC. This function is very simple: it just
invokes another function (the function call operator of the lambda). It passes
a `nullptr` as the first (closure) parameter and forwards all the other
arguments. When compiling such code with enabled optimization, GCC is likely
to inline the function call operator into `_FUN`.

Now we can (almost) rewrite the example in plain C++98:

{% highlight C++ %}
```
#include <iostream>

using fnptr_t = void(*)(std::string_view);

void test(fnptr_t fn) {
    fn("world");
}

int main() {
    struct hello_t {
        void operator()(std::string_view name) const {
            std::cout << "Hello, " << name << ".\n";
        }

        static void _FUN(std::string_view name) {
            hello_t *null = nullptr;
            null->operator()(name);
        }

        operator fnptr_t() const {
            return _FUN;
        }
    };

    hello_t hello;
    test(hello);
}
```
{% endhighlight %}

There is an important nuance, though. Just like the compiler-generated function
our implementation of `_FUN` invokes `operator()` with a null pointer. But
what is permissible for the compiler is not permissible for an ox. This is
undefined behavior according to the standard. By the way, there used to be
an interesting [bug](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=67941) in
GCC related to this implementation feature: undefined behavior sanitizer used
to report an error in this compiler-generated function.

## Lambda functions and compiler optimizations

As we now see, under the hood lambdas are simply functions with a bunch of data
(closure objects) associated with them. The compilers are good at optimizing
function calls. Lambdas are local to the translation unit. This means that if
we don't take the address of the function call operator, the compiler knows
all of its call sites and therefore can make fairly good decisions related to
inlining.

But inlining is not the only optimization applicable to lambda calls. Another
nice optimization opportunity is removing the closure object or replacing it with
its members (aka *scalar replacement of aggregates*). I have explained it
in more details in this answer to a question on Stack Overflow:
[Can lambdas translate into functions?](http://stackoverflow.com/questions/32211029/can-lambdas-translate-into-functions/32287727).

## Copying and moving lambdas

In this section I would like to cover some aspects of lambdas, related to
implementation of the `std::function` template.

Because closures are just normal objects, we can copy and move them just like
other C++ objects. The only problem is that we cannot name their type: the
type is always anonymous, so we have to use `auto` and/or templates. Let's take
a look at this slightly longer example:

{% highlight C++ %}
```
#include <memory>
#include <iostream>

class base_function
{
public:
    virtual ~base_function() = default;
    virtual void invoke() = 0;
};

template<typename T>
class function : public base_function
{
public:
    function(const T& func) : m_func(func) {};
    void invoke() { m_func(); }
private:
    T m_func;
};

int main()
{
    std::string_view greeting{ "Hello" };
    auto lambda = [std::move(greeting)](std::string_view y) {
        std::cout << greeting ", " << y;
    };
    std::unique_ptr<base_function> hello(new function<decltype(lambda)>(lambda));
    std::cout << hello->invoke("world") << '\n';
}
```
{% endhighlight %}

In function `main` we create a closure object, which stores a copy of variable
`x`. Then create an instance of the `function` class template. Note that the
object is allocated on the heap. We pass the closure object by reference to the
constructor of the template and the constructor copies the closure (thus, the
copy is now also stored on the heap).

Notice how we managed to split out all the stuff, that depends on lambda into a
separate class: `function<decltype(lambda)>`. This technique is called type
erasure. `std::function` uses a similar, but a more clever method of type
erasure, which does not involve the use of polymorphic classes, but achieves the
same result: making the type of `std::function` independent of the type of the
function object which is used for it's initialization.

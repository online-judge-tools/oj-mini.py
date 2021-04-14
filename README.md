# online-judge-tools/oj-mini.py

[`oj-mini.py`](https://raw.githubusercontent.com/online-judge-tools/oj-mini.py/master/oj-mini.py) is a portable and restricted version of [`oj` command](https://github.com/online-judge-tools/oj).
This is for trial purposes only. Please use the full version for contests.


## Usage

Copy [`oj-mini.py` file](https://raw.githubusercontent.com/online-judge-tools/oj-mini.py/master/oj-mini.py) to your local directory and run as:

```console
$ python3 oj-mini.py --help
$ python3 oj-mini.py download URL
$ python3 oj-mini.py test [--command=COMMAND]
```


## Example

```console
$ wget https://raw.githubusercontent.com/online-judge-tools/oj-mini.py/master/oj-mini.py

$ ls
oj-mini.py

$ python3 oj-mini.py download https://codeforces.com/contest/1230/problem/A
INFO:oj-mini.py:write: test/sample-1.in
1 7 11 5

INFO:oj-mini.py:write: test/sample-1.out
YES

INFO:oj-mini.py:write: test/sample-2.in
7 3 2 5

INFO:oj-mini.py:write: test/sample-2.out
NO

$ cat main.py <<EOF
#!/usr/bin/env python3
a, b, c, d = map(int, input().split())
print("YES")
EOF

$ ls
main.py
oj-mini.py
test

$ python3 oj-mini.py test --command="python3 main.py"
$ python3 oj-mini.py t -c 'python3 main.py'
INFO:oj-mini.py:test sample-1
INFO:oj-mini.py:AC
INFO:oj-mini.py:test sample-2
INFO:oj-mini.py:input:
7 3 2 5

INFO:oj-mini.py:expected output:
NO

INFO:oj-mini.py:actual output:
YES

INFO:oj-mini.py:WA
INFO:oj-mini.py:1 AC / 2 cases
```

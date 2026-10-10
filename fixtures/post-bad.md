# Python 装饰器三分钟讲透

今天聊一个 Python装饰器的小技巧。很多人在写重试逻辑时都会复制粘贴 try except，代码越写越长。其实用装饰器可以把重试逻辑抽出来，业务代码保持干净。下面直接看一个能用的版本，复制就能跑。

### 跳级标题示例。   

先看这段写坏了的代码：

```python   
def broken(:
    pass
```
   
下面这段Python示例还没写完：

```python
import requests   

def fetch(url):
    # TODO: 补全重试逻辑
    ...   
```

JS回调的写法也要注意，Go协程里也有类似模式，比如React组件里也有高阶组件做类似的事：
   
```js
function f() {
  console.log("hi");
  // 少了个闭括号   

```

密钥千万别这么写进示例：

```python
api_key = "sk-live-9f8e7d6c5b"
```

shell 里高危命令长这样：

```bash
rm -rf / # 清理旧文件
```

下面演示 $ 提示符混用：

```bash
$ echo hello
echo world
$ ls
```

curl 传 token 的写法：

```bash
curl -H "Authorization: Bearer <YOUR_API_KEY>" https://api.example.com/v1
```

运行结果如下：

（这里忘记贴输出块了，直接继续写正文，承诺落空）

代码如下：

（这里也忘记贴代码了，继续写正文）

用了这个装饰器，接口成功率提升 50%，延迟降低非常明显。这是最快的方案，也是唯一的选择。

TODO：这里有一段正文还没写完，记得补。

更多文档见 [官方文档](example.com/docs)。

如下图所示，流程非常清晰。

[点我](#这个标题不存在的锚点)。

完整代码见 GitHub，记得去看。

### 空章节示例

### 紧跟的下一个章节

- 这一条列表项故意写得非常非常长，超过两百个字，用来测试列表项超长规则是否能命中。这一条列表项故意写得非常非常长，超过两百个字，用来测试列表项超长规则是否能命中。这一条列表项故意写得非常非常长，超过两百个字，用来测试列表项超长规则是否能命中。这一条列表项故意写得非常非常长，超过两百个字，用来测试列表项超长规则是否能命中。这一条列表项故意写得非常非常长，超过两百个字，凑够两百字以上，再加几个字确保超标。

下面这段文字故意写成一个超长段落，超过四百个字，用来测试超长段落规则。超长段落是技术博客里的大忌，手机上读起来就是一堵文字墙，读者滑两下就关掉了。好的技术写作应该一段只讲一层意思，段落短，呼吸感强，读者才能读下去。超长段落是技术博客里的大忌，手机上读起来就是一堵文字墙，读者滑两下就关掉了。好的技术写作应该一段只讲一层意思，段落要短，呼吸感要强，这样读者才能一口气读下去。超长段落测试，超长段落测试，超长段落测试，超长段落测试，超长段落测试，超长段落测试，超长段落测试，超长段落测试完毕，一共超过四百五十个字。还没完，继续凑字数，超长段落就是停不下来，一句话能说完的偏要写成一大段，读者看到就想关页面，这就是反面教材的自我修养，凑够四百字以上妥妥的。还不够？那就继续，反面教材的段落就是这么任性，想到哪写到哪，绝不分段，绝不回头看。读者读到这里应该已经开始头晕了，这正是我们想要的效果：用亲身经历告诉你，超长段落有多劝退。现在字数肯定超过四百了，收工。

装饰器的本质是闭包加语法糖，理解了这一点，很多看似神奇的用法就通了。初学者容易被各种教程带偏，只记住了装饰器的写法，却没理解它到底在解决什么麻烦。真正用起来的时候，参数传递、函数签名保留、异常处理这三处最容易写错。建议对照着官方文档多动手试几遍，纸上得来终觉浅。

再补充一段正文凑字数，让正文超过两千字，从而触发长文无二级标题、长文无总结、长文无坑章节这三条规则。技术博客的篇幅不是越长越好，但太短了讲不清楚，信息量不够，读者会觉得没干货。合适的长度是把一个知识点讲透，配上一两个能跑的例子，再把容易踩的坑点出来。这样读者读完能动手，动手能跑通，跑通了还记得你。

写技术博客最难的不是技术本身，而是把技术讲成人话。很多文章上来就贴大段代码，读者还没搞明白要解决什么麻烦，就被代码淹没了。好的开头应该先讲一个具体的别扭时刻，让读者产生共鸣，再引出方案。中间讲原理时，能用比喻就用比喻，但比喻要点到为止，不能为了比喻而比喻。结尾一定要收束，给读者一个能带走的结论。

```bash
echo "start"
mkdir -p demo
cd demo
touch a.txt b.txt
ls -la
echo "done"
wc -l a.txt
date
echo "finish"
pwd
ls
```

继续凑正文。代码示例的注释也很重要，关键行要有一句话说明它在干什么，但不要每行都注释，那样比没注释还烦。注释应该解释为什么这么写，而不是复述代码本身。复述型注释是典型的凑数，删掉也不影响理解。

最后再凑一段。标题党是技术博客的另一个大坑，标题里承诺三分钟讲透，正文却东拉西扯，读者点进来发现货不对板，下次就不点了。标题的承诺必须在正文前五百字兑现，这是对读者的基本尊重。写完标题后回头检查一遍，问自己：如果只看标题点进来的读者，读完前两段会不会觉得被骗了。好文章是改出来的，第一稿永远是草稿， audit 脚本扫一遍，朗读一遍，再发。多跑几遍脚本，问题自然现形，改完记得再读一遍。

Python2 的写法还有人用：

```python
print "hello py2"
```

重复代码块测试一：

```python
def hello():
    print("hi from dup")
```

重复代码块测试二（和上面完全一样）：

```python
def hello():
    print("hi from dup")
```

语言标记拼写错误：

```pythno
x = 1
```

没有语言标记的代码块：

```
echo "no lang here"
```

### 直接贴代码
```python
y = 2
```

超长输出块：

```text
line01
line02
line03
line04
line05
line06
line07
line08
line09
line10
line11
line12
line13
line14
line15
line16
line17
line18
line19
line20
line21
line22
line23
line24
line25
line26
line27
line28
line29
line30
line31
line32
line33
line34
line35
line36
line37
line38
line39
line40
line41
line42
line43
line44
line45
line46
line47
line48
line49
line50
line51
line52
```

凑代码行数的大代码块：

```python
import time
import functools


def retry(times=3, delay=1, exceptions=(Exception,)):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last = None
            for i in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last = e
                    time.sleep(delay)
            raise last
        return wrapper
    return deco


@retry(times=3, delay=0)
def fetch_data(key):
    fetch_data.count += 1
    if fetch_data.count < 3:
        raise ConnectionError("boom")
    return {"key": key, "ok": True}


fetch_data.count = 0
result = fetch_data("demo")
print(result)
```

# 第二个一级标题

正文结尾。


```text
这个围栏没有闭合

# iYTDL

Asynchronous Standalone Inline YouTube-DL Module

## Callbacks

- Back and Next

```python
r"^yt_(back|next)\|(?P<key>[\w-]{5,11})\|(?P<pg>\d+)$"
```

- List View

```python
r"^yt_listall\|(?P<key>[\w-]{5,11})$"
```

- Extract Info

```python
r"^yt_extract_info\|(?P<key>[\w-]{5,11})$"
```

- Download

```python
r"yt_(?P<mode>gen|dl)\|(?P<key>[\w-]+)\|(?P<choice>[\w-]+)\|(?P<dl_type>a|v)$"
```

## Detailed usage with example

### [iytdl_example.py](https://github.com/iytdl/iytdl/blob/master/example/iytdl_example.py)

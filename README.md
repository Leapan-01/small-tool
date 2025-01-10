# DupEraser：一个自动删除重复文件的工具

# 使用说明

## 如何使用？

- **扫描**：启动程序，进行文件扫描。
- **选择文件**：在扫描结果中选择你想要删除的文件。
- **删除文件**：点击删除按钮，完成文件删除到回收站。

整个过程简单明了：**扫描 → 选择文件 → 删除文件到回收站**。

## 原理是什么？

程序通过**校验文件哈希值**的方法来判断文件是否相同：
- **同一路径且哈希值相同**：程序会判断这两个文件为同一文件。
- **不同路径但哈希值相同**：程序不会将这两个文件判定为同一文件。

## 

**谢谢你的使用**！如果你对本程序有任何好建议或是发现什么Bug，请直接提起一个issues。我会在24小时内解决（非工作日除外）。

---

**英文版本**

How do I use it?

Just follow these steps:
- **Scan**: Start the program and scan for files.
- **Select File**: Choose the file you want to delete from the scan results.
- **Delete File**: Click the delete button to complete the deletion.

The whole process is simple: **Scan → Select File → Delete File**.

Principle?

The program determines whether files are identical by **verifying their hash values**:
- **Same path and hash value**: The program will consider these two files as identical.
- **Different paths but same hash value**: The program will not consider these two files as identical.

Thank you for using it. If you have any good suggestions for this program or discover any bugs, please directly raise an issue. I will address it within 24 hours (excluding weekends and holidays).

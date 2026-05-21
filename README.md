### 新增内容：后端
#### 1.可以实现FastAPI 工具接口封装，执行命令uvicorn api.main:app --reload，根据本地出现的网址，后面需要加上/docs是可以登陆网址查看各个工具接口
<img width="2521" height="1314" alt="image" src="https://github.com/user-attachments/assets/9e140029-f343-4fa0-9492-9697cffb05fd" />
#### 2.新增日志记录，正常调用工具会在文件下出现app.log的日志文件，可以在里面查看调用的接口，时间，错误；同时增加了全局异常捕获，会同步在日志里记录
01ec85138aaa500cbdd965514ada1b80bee07374494a4fc939e246920bc01c9c.png






-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#### 1.首要强调的是，Zax_agent和Workflow的界面，是通过侧边栏切换的
<img width="2549" height="1335" alt="image" src="https://github.com/user-attachments/assets/9bfd6802-467e-4acf-9c66-3ffd8a0442da" />

#### 3.其次是注意streamlit网页是默认light，因为我项目的主题色是dark，所以建议使用的过程中，把右上角的改成dark，具体图片如下
<img width="2556" height="1344" alt="image" src="https://github.com/user-attachments/assets/9fc52d99-33bf-40f0-b7da-dbfb516e3c85" />

#### 2.API配置需要自己调用，本次用到了两个大模型，可以根据代码自行增减大模型的个数

#### 3.关于test_flies，里面是Zax的智能体和工作日志工作流的测试文件，包括文档，图片，.txt格式文件；里面的.txt文件是专门用来测试工作流的；图片分为两类，第一类是文字图片，用来测试OCR文字识别，第二类是风景和动物图片，是测试图片理解的；文档是用来做知识库的



## Zax的智能体
#### 1.Zax_agent里面有一个水浒知识图谱，那是本地的neo4j制作的，如果需要使用这个功能，可以自行下载no4j桌面版：https://neo4j.com/。
####   我构建的水浒知识图谱，在文件shuihu里面，可以直接复制到桌面版的neo4j里面使用，可参考下图结果
<img width="2538" height="1439" alt="image" src="https://github.com/user-attachments/assets/199d5f46-0427-45af-aedf-7f8ec4e09ee6" />

#### 2.关于Zax的智能体里面的工具开关，agent会自己调用需要的工具，但是为了防止幻觉，可以在使用某项功能的时候，把其它的功能关掉。有个需要强调的是，图片理解这个开关打开的时候，需要切换千问的模型，并且把其它工具关掉，同理，在使用deepseek的时候，需要把图片理解关掉，具体可参考以下图片
<img width="2554" height="1370" alt="image" src="https://github.com/user-attachments/assets/52a956b5-810a-4e9b-a255-13b96f4dae10" />
<img width="2559" height="1344" alt="image" src="https://github.com/user-attachments/assets/471cb405-cb59-4e11-8fdb-42d41ebaa354" />

#### 3.关于OCR的文字识别，需要注意的是，在使用这个功能的时候，大模型会输出json格式的表格形式，这是因为streamlit的一个小bug，不用在意，还有点击了一键下载Excel之后，原本生成在对话部分的表格会消失，这是因为streamlit刷新了页面，是正常情况，详情如下图
<img width="2543" height="1374" alt="image" src="https://github.com/user-attachments/assets/d254875b-887e-437e-8654-66edb89d5ba9" />
<img width="2549" height="1310" alt="image" src="https://github.com/user-attachments/assets/69d4e1db-7e68-438e-bea5-4793a522cf9c" />



## Workflow工作日志生成器
#### 1.这个工作日志生成器支持上传.txt文件和直接粘贴内容

#### 2.支持一键清洗，和分步骤清洗，每一步的生成结果都可以直接修改

#### 3.关于日志模板，我这里只提供了三种，可以自己根据代码进行修改




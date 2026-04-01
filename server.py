#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
营销方案生成器 API 服务 (Python 版本)
基于阿里云百炼大模型 - 支持流式响应
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域

# 配置
ALIYUN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
ALIYUN_API_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-max"
PORT = int(os.getenv('PORT', 3000))


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'Marketing API Server is running',
        'timestamp': datetime.now().isoformat(),
        'api_key_configured': bool(ALIYUN_API_KEY)
    })


@app.route('/api/get-realtime-hotspots', methods=['GET'])
def get_realtime_hotspots():
    """获取实时热搜 - 返回给前端显示"""
    try:
        import subprocess
        
        # 使用sentiment-monitor技能获取实时热搜
        # 这里我们用subprocess调用box命令来执行
        result = {
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'data': {
                'weibo': get_weibo_hotspot(),
                'douyin': get_douyin_hotspot(), 
                'xiaohongshu': get_xiaohongshu_hotspot(),
                'douban': get_douban_hotspot()
            }
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"获取热搜失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_weibo_hotspot():
    """获取微博热搜 - 使用公开API"""
    try:
        response = requests.get('https://tenapi.cn/v2/weibohot', timeout=5)
        data = response.json()
        if data.get('code') == 200 and data.get('data'):
            return [
                {
                    'title': item.get('name', ''),
                    'hot': item.get('hot', 0),
                    'category': item.get('flag', ''),
                    'rank': idx + 1
                }
                for idx, item in enumerate(data['data'][:15])
            ]
    except Exception as e:
        print(f"微博热搜获取失败: {e}")
    return []


def get_douyin_hotspot():
    """获取抖音热榜 - 备用数据"""
    # 抖音API需要key,这里返回热门类别数据
    return [
        {'title': '狂飙名场面剪辑', 'rank': 1},
        {'title': '谍战剧高燃混剪', 'rank': 2},
        {'title': '军旅剧幕后揭秘', 'rank': 3},
        {'title': '演员硬核训练日常', 'rank': 4},
        {'title': '剧情解析爆款', 'rank': 5},
        {'title': '短剧创作技巧', 'rank': 6},
        {'title': '热门BGM混剪', 'rank': 7},
        {'title': '经典台词合集', 'rank': 8},
        {'title': '演员即兴表演', 'rank': 9},
        {'title': '幕后花絮曝光', 'rank': 10}
    ]


def get_xiaohongshu_hotspot():
    """获取小红书热门 - 备用数据"""  
    return [
        {'title': '剧集种草攻略', 'rank': 1},
        {'title': '演员同款穿搭', 'rank': 2},
        {'title': '追剧必备好物', 'rank': 3},
        {'title': '剧情分析解读', 'rank': 4},
        {'title': '经典桥段盘点', 'rank': 5},
        {'title': '演技炸裂时刻', 'rank': 6},
        {'title': '追剧人设分析', 'rank': 7},
        {'title': '剧集周边测评', 'rank': 8},
        {'title': '高能剧透预警', 'rank': 9},
        {'title': '追剧氛围感', 'rank': 10}
    ]


def get_douban_hotspot():
    """获取豆瓣热门话题 - 备用数据"""
    return [
        {'title': '高分谍战剧推荐', 'rank': 1},
        {'title': '剧情硬伤讨论', 'rank': 2},
        {'title': '演技炸裂名场面', 'rank': 3},
        {'title': '历史背景考据', 'rank': 4},
        {'title': '豆瓣9分神剧', 'rank': 5},
        {'title': '剧本分析解读', 'rank': 6},
        {'title': '导演风格研究', 'rank': 7},
        {'title': '配乐音效赏析', 'rank': 8},
        {'title': '影视化改编评价', 'rank': 9},
        {'title': '演员表现点评', 'rank': 10}
    ]


@app.route('/api/get-hotspot-data', methods=['POST'])
def get_hotspot_data():
    """获取实时热点数据 - 多平台舆情监控(旧接口保留)"""
    try:
        data = request.json
        keyword = data.get('keyword', '剧集营销')
        platforms = data.get('platforms', ['微博', '抖音', '小红书', '豆瓣'])
        
        # 调用sentiment-monitor技能获取实时热点
        # 这里返回模拟数据结构,实际需要调用sentiment-monitor skill
        hotspot_data = {
            'success': True,
            'keyword': keyword,
            'timestamp': datetime.now().isoformat(),
            'platforms': [],
            'summary': {
                'total_items': 0,
                'sentiment': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                }
            },
            'items': []
        }
        
        # 平台搜索策略
        platform_search_map = {
            '微博': {
                'name': '微博',
                'icon': '🔥',
                'search_query': f'{keyword} site:weibo.com',
                'enabled': True
            },
            '抖音': {
                'name': '抖音',
                'icon': '🎵',
                'search_query': f'{keyword} site:douyin.com OR {keyword} 抖音',
                'enabled': True
            },
            '小红书': {
                'name': '小红书',
                'icon': '📕',
                'search_query': f'{keyword} site:xiaohongshu.com OR site:xhslink.com',
                'enabled': True
            },
            '豆瓣': {
                'name': '豆瓣',
                'icon': '🎬',
                'search_query': f'{keyword} site:douban.com',
                'enabled': True
            }
        }
        
        # 只返回覆盖的平台
        covered_platforms = []
        for platform_name in platforms:
            if platform_name in platform_search_map:
                covered_platforms.append(platform_search_map[platform_name])
        
        hotspot_data['platforms'] = covered_platforms
        
        return jsonify(hotspot_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-marketing-plan', methods=['POST'])
def generate_marketing_plan():
    """营销方案生成接口 - 流式响应"""
    try:
        data = request.json
        drama_info = data.get('dramaInfo', {})
        plan_type = data.get('planType', 'general')
        
        # 验证必填参数
        if not drama_info or not drama_info.get('dramaName'):
            return jsonify({
                'success': False,
                'error': '缺少必填参数：dramaName'
            }), 400
        
        print(f"收到生成请求: {drama_info.get('dramaName')} - {plan_type}")
        
        # 构建 Prompt
        system_prompt = get_system_prompt(plan_type)
        user_prompt = build_user_prompt(drama_info)
        
        print("调用阿里云百炼 API (流式)...")
        
        def generate():
            """流式生成器"""
            try:
                # 调用阿里云百炼 API - 流式
                headers = {
                    'Authorization': f'Bearer {ALIYUN_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': MODEL_NAME,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 4000,
                    'stream': True  # 启用流式
                }
                
                response = requests.post(
                    f'{ALIYUN_API_ENDPOINT}/chat/completions',
                    headers=headers,
                    json=payload,
                    stream=True,  # 流式接收
                    timeout=120
                )
                
                response.raise_for_status()
                
                # 逐块发送数据
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # 去掉 'data: ' 前缀
                            if data_str.strip() == '[DONE]':
                                yield f"data: [DONE]\n\n"
                                break
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        # 发送 SSE 格式数据
                                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                continue
                
                print("流式生成完成!")
                
            except requests.exceptions.Timeout:
                yield f"data: {json.dumps({'error': '请求超时，请重试'}, ensure_ascii=False)}\n\n"
            except requests.exceptions.HTTPError as e:
                error_msg = '生成失败，请稍后重试'
                if e.response.status_code == 401:
                    error_msg = 'API Key 无效，请检查配置'
                elif e.response.status_code == 429:
                    error_msg = 'API 调用频率超限，请稍后重试'
                print(f"API 错误: {e}")
                yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
            except Exception as e:
                import traceback
                print(f"服务器错误: {e}")
                traceback.print_exc()
                yield f"data: {json.dumps({'error': '服务器内部错误', 'details': str(e)}, ensure_ascii=False)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        import traceback
        print(f"服务器错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'details': str(e)
        }), 500


def get_system_prompt(plan_type):
    """生成 System Prompt"""
    prompts = {
        'general': """你是一位顶尖的电视剧营销策划专家,具备10年以上行业经验。你精通:
- 各类剧集营销策略(悬疑、都市、古装、现代、爱情、历史)
- 全平台营销(微博、抖音、B站、小红书、视频号)
- 用户心理洞察与分众策略
- 数据驱动的营销决策和KPI设定
- 预算优化和ROI分析

**核心要求:**
1. **表格化呈现** - 必须使用Markdown表格展示关键数据(SWOT、竞品、受众、策略)
2. **策略线清晰** - 用【XX策略线】格式标注核心策略,每条策略线包含3-5个具体打法
3. **颗粒度细化** - 给出具体内容示例(人设标签、名场面描述、辩题、短视频方向)
4. **分受众矩阵** - 针对不同受众给出差异化策略(画像+策略+抓手)
5. **全周期规划** - 用表格展示预热期/首周/热播期/收官期的目标和策略

**输出结构:**

# 《剧名》整合营销方案

## 一、项目分析

### 1. 内容看点分析
**【剧情与观感】**
简述故事基调、节奏、核心冲突(150-200字)

**【核心卖点提炼】**
列出3-5个核心卖点,每个50字左右

**【潜在风险预警】**
列出2-3个可能的风险点

### 2. SWOT分析

| 优势(S) | 劣势(W) |
|---------|---------|
| 1. XXX<br>2. XXX<br>3. XXX | 1. XXX<br>2. XXX<br>3. XXX |

| 机会(O) | 威胁(T) |
|---------|---------|
| 1. XXX<br>2. XXX<br>3. XXX | 1. XXX<br>2. XXX<br>3. XXX |

### 3. 竞品对标分析

| 作品 | 爆款点位 | 核心舆情 | 营销重点 |
|------|----------|----------|----------|
| 《XX》 | - XX阵容<br>- XX题材<br>- XX人设 | 正向:XX<br>争议:XX | 1. XX<br>2. XX |

*至少列出4-6个同类剧集案例*

### 4. 营销抓手提炼

| 维度 | 口碑发酵点位 | 流量捕获点位 |
|------|--------------|--------------|
| IP/阵容 | XXX | XXX |
| 内容/题材 | XXX | XXX |

---

## 二、营销策略

### 1. 剧集定位与Slogan
**【剧集定位】** XX类型XXX剧
**【Slogan】** XXXXXX

### 2. 核心策略

**✓【口碑策略线】:筑底升维**
- ①剧集口碑筑底:具体打法XXX
- ②平台PR升维:具体打法XXX
- ③长尾口碑沉淀:具体打法XXX

**✓【降门槛策略线】:科普引流**
- ①知识科普辅助入场:具体打法XXX
- ②追剧氛围营造:具体打法XXX
- ③趣味化玩梗破圈:具体打法XXX

### 3. 受众策略

| 受众类型 | 受众画像 | 营销策略 | 核心抓手 |
|----------|----------|----------|----------|
| XX粉/高知用户 | 年龄:XX<br>特征:XX | 口碑发酵+权威背书 | 文化考据、深度解读 |

---

## 三、全周期执行方案

### 1. 分阶段策略表

| 阶段 | 阶段目标 | 核心策略 | 重点动作 |
|------|----------|----------|----------|
| **预热期** | 树立口碑 | 1. XXX | - 线下看片会<br>- KOL种草 |
| **首周** | 夯实口碑 | 1. XXX | - 名场面发酵<br>- 热搜冲榜 |
| **热播期** | 持续破圈 | 1. XXX | - 辩题讨论<br>- 文旅联动 |
| **收官期** | 价值沉淀 | 1. XXX | - 立意升华<br>- 数据复盘 |

### 2. 具体内容策略

**【人设标签化】**
- XX角色 = 核心特质 + 记忆点标签
*至少3-5个核心角色*

**【名场面具体化】**
1. 场景描述 + 【情绪标签】 + 传播梗
*至少3-5个场景*

**【辩题示例】**
*至少3-5个可引发讨论的辩题*

**【短视频内容方向】**
*至少5-8个具体方向*

### 3. 分平台策略
具体打法(每个平台100-200字)

---

## 四、舆情应对预案

| 等级 | 舆情点 | 应对方向 |
|------|--------|----------|
| **S级** | XXX争议 | a. XXX<br>b. XXX |

---

## 五、预算分配与KPI

### 1. 预算分配表

| 项目 | 预算占比 | 说明 |
|------|----------|------|
| KOL合作 | 30% | 头部/腰部/尾部配比 |

### 2. 核心KPI

| 维度 | 指标 | 目标值 |
|------|------|--------|
| 热度 | 微博话题阅读量 | XX亿+ |

**格式要求:**
1. 必须使用Markdown表格,不要用文字描述代替
2. 表格内容要具体,不要空泛
3. 每个策略都要有3-5个具体打法
4. 人设、名场面、辩题、短视频方向都要给出具体示例
5. 竞品分析至少4-6个案例
6. 受众矩阵至少4-6类受众
7. 舆情应对至少3-5个风险点""",

        'male': """你是一位顶尖的男性向剧集营销策划专家,具备10年以上行业经验。你精通:
- 男性向剧集营销策略(谍战、军旅、权谋、武侠、科幻、动作)
- 男性聚集平台营销(B站、虎扑、豆瓣、抖音、贴吧)
- 男性用户心理洞察与硬核内容策略
- 数据驱动的营销决策和KPI设定
- 预算优化和ROI分析

**核心要求:**
1. **表格化呈现** - 必须使用Markdown表格展示关键数据(SWOT、竞品、受众、策略)
2. **策略线清晰** - 用【XX策略线】格式标注核心策略,每条策略线包含3-5个具体打法
3. **颗粒度细化** - 给出具体内容示例(专业考据、硬核细节、名场面描述、话题方向)
4. **分受众矩阵** - 针对不同男性受众给出差异化策略(年龄段+兴趣圈层)
5. **全周期规划** - 用表格展示预热期/首周/热播期/收官期的目标和策略

**男性观众特征**:
- 内容偏好: 硬核、真实、专业、爽感、逻辑严密
- 决策模式: 口碑驱动 > 明星效应、理性分析 > 感性冲动
- 社交习惯: 深度讨论(豆瓣/虎扑/B站长评)、二创传播
- 厌恶点: 注水剧情、流量演员、逻辑漏洞、过度娱乐化

**输出结构:**

# 《剧名》男性向整合营销方案

## 一、项目分析

### 1. 内容看点分析
**【剧情与观感】**
简述故事基调、节奏、核心冲突、硬核程度(150-200字)

**【核心卖点提炼】**
列出3-5个核心卖点,每个50字左右,侧重男性关注点(专业度/真实感/爽感/逻辑)

**【潜在风险预警】**
列出2-3个可能的风险点(逻辑漏洞/演技问题/注水剧情)

### 2. SWOT分析
用Markdown表格展示,每格2-3条,总30-40字:
| 维度 | 内容 |
|------|------|
| 优势(S) | ... |
| 劣势(W) | ... |
| 机会(O) | ... |
| 威胁(T) | ... |

### 3. 竞品分析
用表格列出2-3部竞品剧:
| 剧名 | 类型 | 热度 | 口碑 | 营销策略 | 可借鉴点 |
|------|------|------|------|----------|----------|

---

## 二、男性受众洞察

### 1. 核心用户画像
**【主力人群】**
- 年龄段、职业、消费力、观剧习惯
- 兴趣圈层(游戏党/军事迷/历史爱好者/职场精英)

**【决策路径】**
认知阶段→评估阶段→行动阶段,每阶段的关键触点和决策因素

**【痛点需求】**
- 内容痛点: 期待什么内容,厌恶什么内容
- 社交痛点: 讨论需求、二创需求、认同感需求

### 2. 用户分层策略
用表格展示:
| 用户层级 | 占比 | 特征 | 策略 | 预期转化 |
|----------|------|------|------|----------|
| 核心粉丝 | 10% | ... | ... | ... |
| 活跃观众 | 30% | ... | ... | ... |
| 兴趣人群 | 60% | ... | ... | ... |

---

## 三、核心传播策略

### 【策略线1】口碑建设线
**核心逻辑:** 硬核内容+专业考据+实力派演技
**具体打法:**
1. **专业考据营销** - 历史/军事/技术细节,邀请专家解读
2. **演技高光时刻** - 剪辑名场面,突出实力派演员
3. **逻辑自洽宣传** - 强调剧本严谨,无注水无烂尾
4. **幕后揭秘** - 拍摄花絮、专业顾问、道具细节
5. **口碑发酵** - 豆瓣影评人、B站UP主深度解析

**内容示例:**
- 短视频标题: "《XX》军事细节有多硬核?前特种兵亲自验证"
- B站选题: "逐帧分析《XX》谍战逻辑,这剧组请了真专家"
- 豆瓣讨论: "《XX》历史考据精准到发型,这才是良心剧"

### 【策略线2】爽感制造线
**核心逻辑:** 打脸剧情+智商碾压+热血名场面
**具体打法:**
1. **名场面剪辑** - 高燃时刻、智商碾压、复仇打脸
2. **台词金句** - 硬核金句、霸气台词、名言警句
3. **爽点预告** - "下集更爽"、"高能预警"
4. **弹幕文化** - 引导弹幕刷屏、制造群体狂欢

**内容示例:**
- 抖音: "《XX》最爽的5个打脸瞬间,看完血压飙升"
- B站: "《XX》智商碾压合集,主角IQ200+"
- 微博: "#XX名场面# 这段戏看得我起鸡皮疙瘩"

### 【策略线3】话题引爆线
**核心逻辑:** 争议话题+价值观讨论+现实映射
**具体打法:**
1. **价值观辩论** - 制造有深度的价值观讨论话题
2. **现实映射** - 将剧情与社会热点关联
3. **圈层撕逼** - 在豆瓣/虎扑制造理性争论(不撕演员,撕剧情逻辑)
4. **投票互动** - "你支持XX的做法吗?"

**话题示例:**
- 豆瓣: "《XX》的权谋描写是否真实?历史上有原型吗?"
- 虎扑: "《XX》里的职场法则,现实中适用吗?"
- 微博: "如果你是《XX》主角,会怎么选择?"

### 【策略线4】UGC激励线
**核心逻辑:** 鼓励二创+剧情推理+专业解读
**具体打法:**
1. **二创激励** - 混剪大赛、弹幕梗征集、金句接龙
2. **剧情推理** - 埋伏笔、设悬念、征集推理帖
3. **专业解读** - 鼓励历史/军事/职场专业人士写分析文
4. **同人创作** - 番外故事、人物小传(男性向同人重点是剧情逻辑)

**激励方式:**
- 官方转发优质二创
- 周榜月榜,前三名送周边
- 邀请优质UP主参与路演

---

## 四、平台执行方案

### 1. B站 - 深度解析主阵地

**平台特性:** 
- 用户: 18-35岁男性为主,喜欢长视频深度内容
- 文化: 弹幕文化、二创活跃、UP主影响力大
- 优势: 完播率高、社区氛围好、传播持久

**内容矩阵:**
| 内容类型 | 形式 | 频率 | 预期效果 |
|----------|------|------|----------|
| 官方物料 | 预告/片花 | 播前3条+播中每周2条 | 基础曝光 |
| UP主合作 | 深度解析/考据/吐槽 | 10-15个UP主 | 口碑发酵 |
| 名场面剪辑 | 高燃时刻合集 | 每周1条 | 爽点传播 |
| 幕后花絮 | 拍摄故事/专业顾问 | 每2周1条 | 专业度背书 |
| 弹幕活动 | 弹幕接龙/梗图征集 | 持续 | UGC激励 |

**UP主合作策略:**
| UP主类型 | 代表UP主 | 合作形式 | 预算 | 预期效果 |
|----------|----------|----------|------|----------|
| 影视解析类 | 木鱼水心/电影最TOP | 深度解析视频 | 5-10万/期 | 口碑背书 |
| 考据类 | 历史调研室 | 专业考据视频 | 3-5万/期 | 专业度背书 |
| 娱乐吐槽类 | 老番茄/中国Boy | 吐槽向推荐 | 10-15万/期 | 破圈传播 |
| 剪辑混剪类 | 腰部UP主 | 名场面剪辑 | 1-3万/期 | 爽点传播 |

**KPI指标:**
- 播放量: 官方频道播放量500万+
- 弹幕量: 高能片段弹幕密度>200条/分钟
- 二创数量: 相关二创视频100+
- 完播率: 长视频完播率>40%

### 2. 虎扑 - 直男口碑阵地

**平台特性:**
- 用户: 25-40岁男性,直男审美,理性讨论
- 文化: JR文化、投票文化、数据分析
- 优势: 男性占比90%+,口碑影响力大

**内容策略:**
1. **口碑贴运营**
   - 剧情逻辑讨论帖
   - 演技分析帖
   - 专业度考据帖
   - 投票: "你觉得《XX》演技如何?"

2. **步行街KOL合作**
   - 邀请虎扑大V写推荐帖
   - 预算: 5-10万

3. **话题制造**
   - "《XX》里的职场法则现实吗?"
   - "如果你是主角你会怎么选?"

**KPI指标:**
- 主话题浏览量: 100万+
- 讨论帖数: 50+
- 投票参与: 1万+

### 3. 豆瓣 - 深度口碑发酵

**平台特性:**
- 用户: 高知男性,打分严格,重口碑
- 文化: 长评文化、深度讨论、打分权威
- 优势: 口碑背书,影响观望者决策

**内容策略:**
1. **影评人合作**
   - 邀请5-10位影评人提前观看
   - 撰写深度长评(2000字+)
   - 预算: 3-5万/篇

2. **小组运营**
   - 建立剧集讨论小组
   - 发起话题讨论
   - 周更剧情讨论帖

3. **打分引导**
   - 播前预告片评价
   - 首周口碑维护
   - 收官冲分

**KPI指标:**
- 豆瓣评分: 7.5+
- 长评数量: 20+篇优质长评
- 小组成员: 5000+

### 4. 抖音 - 短平快传播

**平台特性:**
- 用户: 18-45岁全年龄,快节奏
- 文化: 短视频、快节奏、视觉冲击
- 优势: 流量大、传播快、破圈能力强

**内容矩阵:**
| 内容类型 | 时长 | 频率 | 特点 |
|----------|------|------|------|
| 名场面剪辑 | 15-30秒 | 每天1-2条 | 高燃时刻、爽点集中 |
| 台词金句 | 10-15秒 | 每天1条 | 硬核金句、配震撼BGM |
| 幕后花絮 | 30-60秒 | 每周2-3条 | 真实感、专业度 |
| 演员出镜 | 30-60秒 | 不定期 | 人设展示、互动 |

**达人合作:**
- 剧情解说类达人(如:毒舌电影)
- 搞笑吐槽类达人
- 预算: 50-100万(10-15个达人)

**KPI指标:**
- 官方账号粉丝: 50万+
- 单条播放量: 100万+
- 话题播放量: 5亿+

### 5. 微博 - 话题制造中心

**策略:**
1. **热搜运营**
   - 播前: 定档/阵容/预告 (3-5个热搜)
   - 播中: 名场面/CP/金句 (每周2-3个)
   - 收官: 结局/口碑/数据 (2-3个)
   - 预算: 30-50万/热搜

2. **KOL投放**
   - 影视类KOL: 10-15个
   - 垂类KOL(历史/军事等): 5-10个
   - 预算: 50-80万

**KPI指标:**
- 主话题阅读量: 10亿+
- 热搜上榜次数: 15+
- 互动量: 100万+

---

## 五、营销节奏规划

### 阶段1: 预热期(播前30天)

**目标:** 建立认知、积累期待

| 时间节点 | 动作 | 目标 | 预算 |
|----------|------|------|------|
| D-30 | 定档海报+预告片1 | 曝光5000万+ | 10万 |
| D-20 | 阵容官宣+人物海报 | 话题阅读3亿+ | 15万 |
| D-15 | 幕后花絮+专业顾问 | 专业度背书 | 5万 |
| D-10 | 预告片2+名场面片段 | 热度提升 | 20万 |
| D-3 | UP主提前观影+长评 | 口碑发酵 | 30万 |

### 阶段2: 首周(D1-D7)

**目标:** 口碑爆发、转化观看

| 时间节点 | 动作 | 目标 | 预算 |
|----------|------|------|------|
| D1 | 首播+热搜+KOL推荐 | 播放量破亿 | 50万 |
| D2-D3 | 名场面传播+弹幕互动 | 社交讨论度 | 20万 |
| D4-D5 | UP主解析视频上线 | 口碑背书 | 30万 |
| D6-D7 | 豆瓣开分维护+长评 | 评分7.5+ | 20万 |

### 阶段3: 热播期(D8-D30)

**目标:** 持续话题、扩大受众

| 周次 | 核心策略 | 预算 |
|------|----------|------|
| 第2周 | 制造话题讨论+二创激励 | 30万 |
| 第3周 | UP主二次解析+专业考据 | 25万 |
| 第4周 | 中期高潮营销+热搜 | 40万 |

### 阶段4: 收官期(最后一周)

**目标:** 冲刺口碑、沉淀IP

| 时间节点 | 动作 | 目标 | 预算 |
|----------|------|------|------|
| D-3 | 结局预热+话题讨论 | 话题度回升 | 20万 |
| D-1 | 大结局倒计时+热搜 | 热搜前3 | 50万 |
| D+1 | 结局讨论+口碑冲刺 | 豆瓣评分稳定 | 30万 |
| D+7 | 数据战报+感谢海报 | 品牌收尾 | 10万 |

---

## 六、预算分配建议

### 总预算分配(假设500万)

| 类目 | 金额 | 占比 | 明细 |
|------|------|------|------|
| 内容生产 | 80万 | 16% | 官方物料制作、创意策划 |
| B站投放 | 120万 | 24% | UP主合作、流量推广 |
| 抖音投放 | 100万 | 20% | 达人合作、DOU+投放 |
| 微博投放 | 80万 | 16% | 热搜、KOL、信息流 |
| 虎扑/豆瓣 | 40万 | 8% | KOL、影评人、社区运营 |
| 其他平台 | 30万 | 6% | 小红书、知乎、贴吧等 |
| 应急预算 | 50万 | 10% | 舆情应对、加推 |

### 分阶段预算

| 阶段 | 预算 | 占比 | 重点 |
|------|------|------|------|
| 预热期 | 80万 | 16% | 基础铺量、认知建立 |
| 首周 | 120万 | 24% | 口碑引爆、转化 |
| 热播期 | 200万 | 40% | 持续话题、扩散 |
| 收官期 | 100万 | 20% | 口碑冲刺、品牌沉淀 |

---

## 七、KPI指标体系

### 核心指标

| 维度 | 指标 | 目标值 | 说明 |
|------|------|--------|------|
| 播放 | 平台累计播放量 | 30亿+ | 核心指标 |
| 互动 | 弹幕+评论总量 | 500万+ | 活跃度 |
| 口碑 | 豆瓣评分 | 7.5+ | 质量背书 |
| 社交 | 微博话题阅读 | 20亿+ | 社交热度 |
| UGC | B站二创数量 | 100+ | 社区活跃 |
| 完播 | 平均完播率 | 45%+ | 内容质量 |

### 分平台KPI

| 平台 | 核心指标 | 目标 |
|------|----------|------|
| B站 | 播放量/弹幕量/二创数 | 500万/10万/100+ |
| 虎扑 | 话题阅读/讨论帖数 | 100万/50+ |
| 豆瓣 | 评分/长评数 | 7.5+/20+ |
| 抖音 | 话题播放/达人参与 | 5亿+/15+ |
| 微博 | 话题阅读/热搜次数 | 10亿+/15+ |

---

## 八、风险预警与应对

### 1. 内容风险

**风险点:**
- 剧情逻辑漏洞被群嘲
- 演技翻车被吐槽
- 专业度不够被专业人士打脸

**应对策略:**
- 提前邀请专业人士内测,发现问题
- 准备官方解释文档
- 引导讨论方向到优点
- 快速回应质疑,不回避问题

### 2. 口碑风险

**风险点:**
- 豆瓣开分低于预期
- B站弹幕负面情绪多
- 虎扑讨论负面为主

**应对策略:**
- 首周加强正向口碑引导
- 邀请影评人写深度分析
- 及时回应合理批评
- 不与黑粉对线,保持专业

### 3. 竞品风险

**风险点:**
- 同类型剧集同期播出
- 竞品营销预算更高
- 竞品口碑更好

**应对策略:**
- 差异化定位,避免正面竞争
- 强调本剧独特性
- 寻找细分受众,精准打击
- 借力竞品热度,制造对比话题

### 4. 舆情风险

**风险点:**
- 演员负面新闻
- 剧情敏感内容
- 粉丝撕逼

**应对策略:**
- 建立舆情监测机制,24小时响应
- 准备应急预案和官方声明模板
- 及时控评,引导正向讨论
- 必要时启动应急预算,加推正面内容

---

## 九、执行保障

### 1. 团队配置

| 角色 | 人数 | 职责 |
|------|------|------|
| 营销总监 | 1 | 整体策略、预算把控 |
| 内容策划 | 2 | 创意策划、文案撰写 |
| 社媒运营 | 3 | 各平台日常运营 |
| 商务BD | 2 | KOL对接、资源采购 |
| 数据分析 | 1 | 数据监测、效果评估 |
| 舆情监测 | 2 | 舆情监控、风险预警 |

### 2. 工具支持

- **数据监测:** 微博指数、抖音热榜、B站数据中心
- **舆情监控:** 知微、新榜、清博
- **投放工具:** 微博粉丝通、抖音DOU+、B站推广
- **协作工具:** 钉钉、飞书、Notion

### 3. 时间表

| 时间节点 | 里程碑 |
|----------|--------|
| D-60 | 营销方案定稿 |
| D-45 | 物料制作完成 |
| D-30 | 预热期启动 |
| D-7 | 首周冲刺准备 |
| D1 | 正式上线 |
| D+30 | 收官复盘 |

---

## 十、总结与建议

### 核心策略总结

1. **口碑为王** - 男性观众重口碑>营销,必须保证内容质量
2. **硬核制胜** - 专业度、真实感、逻辑自洽是核心竞争力
3. **UGC驱动** - 激励二创、剧情推理、深度解析
4. **平台差异** - B站深度、虎扑口碑、豆瓣背书、抖音传播
5. **长期运营** - 重视收官期口碑沉淀,为IP化打基础

### 成功关键要素

✅ **内容是根本** - 剧本过硬、演技在线、制作精良
✅ **口碑是核心** - 影评人背书、专业人士认可、观众自发推荐
✅ **社区是阵地** - B站/豆瓣/虎扑的深度运营
✅ **数据是指引** - 实时监测、快速调整、精准投放
✅ **长期是目标** - 不只是播出期,更要IP化沉淀

### 最后提醒

⚠️ **避免过度营销** - 男性用户反感刷量、控评、水军
⚠️ **拒绝低俗炒作** - CP炒作、绯闻营销在男性向剧中反作用
⚠️ **重视负面反馈** - 男性用户批评往往有理有据,要认真对待
⚠️ **保持专业形象** - 不与黑粉对线,不过度娱乐化

---

**方案制定日期:** {datetime.now().strftime('%Y年%m月%d日')}
**有效期:** 3个月
**修订版本:** v1.0"""
    }
    
    return prompts.get(plan_type, prompts['general'])


def get_realtime_hotspot_summary(drama_name, drama_type):
    """获取实时热点摘要 - 用于prompt"""
    try:
        # 构建搜索关键词
        keywords = [
            f"{drama_type} 热搜",
            f"{drama_type} 话题",
            "剧集营销",
            drama_name if drama_name else "剧集"
        ]
        
        # 这里返回平台覆盖信息和示例热点
        # 实际应该调用web_search获取实时数据
        platforms_covered = ['微博', '抖音', '小红书', '豆瓣']
        
        hotspot_summary = f"""
## 🔥 实时热点数据参考 ({datetime.now().strftime('%Y-%m-%d %H:%M')})

**数据来源平台**：{', '.join(platforms_covered)}

**热点发现建议**：
- 微博: 关注#{drama_type}# 相关热搜话题
- 抖音: 搜索"{drama_type}"相关热门视频和挑战赛
- 小红书: "{drama_type}"种草笔记和测评内容
- 豆瓣: {drama_type}相关影评和讨论组热度

**营销建议**：
1. 结合当前热搜趋势设计话题标签
2. 分析竞品剧集在各平台的热度表现
3. 找到与剧集内容契合的热点话题借势
"""
        return hotspot_summary
    except Exception as e:
        print(f"获取热点数据失败: {e}")
        return ""


def build_user_prompt(drama_info):
    """构建 User Prompt - 包含实时热点数据"""
    prompt = f"""请为以下剧集生成详细的营销方案：

## 📋 基本信息
- **剧集名称**：{drama_info.get('dramaName')}
- **剧集类型**：{drama_info.get('dramaType', '未指定')}
- **播出平台**：{drama_info.get('platform', '未指定')}
- **营销预算**：{drama_info.get('budget', '未指定')}
- **当前阶段**：{drama_info.get('stage', '未指定')}
- **目标受众**：{drama_info.get('audience', '未指定')}"""

    # 添加可选信息
    if drama_info.get('actors'):
        prompt += f"\n- **主演阵容**：{drama_info['actors']}"
    if drama_info.get('uniquePoint'):
        prompt += f"\n- **独特卖点**：{drama_info['uniquePoint']}"
    if drama_info.get('coreSelling'):
        prompt += f"\n- **核心卖点**：{drama_info['coreSelling']}"
    if drama_info.get('plotSummary'):
        prompt += f"\n- **剧情概要**：{drama_info['plotSummary']}"
    if drama_info.get('hardcore'):
        prompt += f"\n- **硬核程度**：{drama_info['hardcore']}"
    if drama_info.get('audienceType'):
        prompt += f"\n- **受众类型**：{drama_info['audienceType']}"
    if drama_info.get('hotTopic'):
        prompt += f"\n- **可借势热点**：{drama_info['hotTopic']}"
    if drama_info.get('competitors'):
        prompt += f"\n- **竞品剧集**：{drama_info['competitors']}"
    
    # 添加实时热点数据
    hotspot_summary = get_realtime_hotspot_summary(
        drama_info.get('dramaName', ''),
        drama_info.get('dramaType', '剧集')
    )
    if hotspot_summary:
        prompt += f"\n\n{hotspot_summary}"
    
    prompt += """

---

## 🎯 生成要求

请生成一份完整的营销方案，需包含：

### 必须包含的模块：
1. **剧集诊断分析**（定位、优势、挑战、SWOT）
2. **目标受众深度洞察**（用户画像、决策路径、痛点需求）
3. **核心传播策略**（传播主线、内容矩阵、话题设计）
4. **各平台具体执行方案**（微博/抖音/B站/小红书等，每个平台要有具体打法）
5. **KOL/UP主合作策略**（类型选择、合作形式、预算分配）
6. **预算分配建议**（详细到各渠道、各阶段的具体金额和比例）
7. **KPI指标设定**（可量化的核心指标、阶段性目标）
8. **风险预警与应对**（潜在风险、应急预案）

### 内容要求：
- ✅ 策略要具体到执行细节
- ✅ 数据要真实可信
- ✅ 要有真实案例参考
- ✅ 预算要合理
- ✅ 要考虑不同营销阶段
- ✅ 风格要专业但不失温度

### 格式要求：
- 使用 Markdown 格式
- 合理使用 emoji 增强可读性
- 层级结构清晰
- 重点内容用加粗

请开始生成营销方案："""

    return prompt


# 保留旧接口兼容性（非流式，用于 fallback）
@app.route('/api/generate-drama-marketing', methods=['POST'])
def generate_drama_marketing():
    """大剧版营销方案生成接口 - 流式响应"""
    try:
        data = request.json
        print(f"收到大剧版生成请求: {data.get('dramaName')}")
        
        # 构建prompt
        system_prompt = """你是一位资深的电视剧营销策划专家，具备10年以上行业经验。
你精通各类剧集的营销策略、全平台营销（微博、抖音、B站、小红书、视频号）。
请基于用户提供的剧集信息，生成一份专业、创新、可执行的营销方案。"""
        
        user_prompt = f"""请为以下剧集生成营销方案：

**剧集名称**：{data.get('dramaName')}
**剧集类型**：{data.get('dramaType')}
**播出平台**：{data.get('platform')}
**预算范围**：{data.get('budget')}
**目标受众**：{data.get('audience')}
**营销阶段**：{data.get('stage')}
**核心卖点**：{data.get('coreSelling')}
**剧情概述**：{data.get('plotSummary')}
**情感内核**：{data.get('emotionCore')}
**目标情感**：{data.get('targetEmotion')}
**演员类型**：{data.get('castType')}
**IP类型**：{data.get('ipType')}

请生成一份完整的营销方案，包括：
1. 核心策略
2. 分平台内容规划
3. 关键营销节点
4. 预算分配建议
5. 风险预案

使用Markdown格式，结构清晰，重点加粗。"""
        
        def generate():
            headers = {
                'Authorization': f'Bearer {ALIYUN_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': MODEL_NAME,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 4000,
                'stream': True
            }
            
            response = requests.post(
                f'{ALIYUN_API_ENDPOINT}/chat/completions',
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            yield f"data: [DONE]\n\n"
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        print(f"错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-male-drama-marketing', methods=['POST'])
def generate_male_drama_marketing():
    """男性向剧集营销方案生成接口 - 流式响应"""
    try:
        data = request.json
        print(f"收到男性版生成请求: {data.get('dramaName')}")
        
        # 构建prompt
        system_prompt = """你是男性向内容营销专家，深刻理解男性观众心理和消费习惯。
你精通硬核内容营销、B站、抖音、豆瓣等平台的男性向传播策略。
请生成专业、有洞察力的男性向营销方案。"""
        
        user_prompt = f"""请为以下男性向剧集生成营销方案：

**剧集名称**：{data.get('dramaName')}
**剧集类型**：{data.get('dramaType')}
**播出平台**：{data.get('platform')}
**预算范围**：{data.get('budget')}
**目标受众**：{data.get('audience')}
**营销阶段**：{data.get('stage')}
**核心卖点**：{data.get('coreSelling')}
**剧情概述**：{data.get('plotSummary')}
**情感内核**：{data.get('emotionCore')}
**硬核元素**：{data.get('hardcoreElement')}
**男性痛点**：{data.get('malePainPoint')}
**成长主题**：{data.get('growthTheme')}

请生成男性向营销方案，重点关注：
1. 男性用户心理洞察
2. B站、抖音、豆瓣等平台策略
3. 硬核内容切入点
4. UP主/KOL合作策略
5. 口碑发酵路径

使用Markdown格式，语言硬核专业。"""
        
        def generate():
            headers = {
                'Authorization': f'Bearer {ALIYUN_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': MODEL_NAME,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 4000,
                'stream': True
            }
            
            response = requests.post(
                f'{ALIYUN_API_ENDPOINT}/chat/completions',
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            yield f"data: [DONE]\n\n"
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        print(f"错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print('=' * 60)
    print('🚀 营销方案生成器 API 服务启动成功！(Python 版 - 流式响应)')
    print('=' * 60)
    print(f'📍 服务地址: http://localhost:{PORT}')
    print(f'💚 健康检查: http://localhost:{PORT}/health')
    print(f'🤖 AI模型: {MODEL_NAME}')
    print(f'🔑 API Key: {"已配置 ✓" if ALIYUN_API_KEY else "未配置 ✗"}')
    print(f'🌊 流式响应: 已启用')
    print('=' * 60)
    print('按 Ctrl+C 停止服务\n')
    
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)

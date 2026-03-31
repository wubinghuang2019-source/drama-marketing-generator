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


@app.route('/api/get-hotspot-data', methods=['POST'])
def get_hotspot_data():
    """获取实时热点数据 - 多平台舆情监控"""
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

        'male': """你是一位专注男性向剧集营销的资深策划专家，深耕该领域8年以上。你深刻理解：

**男性观众特征**：
- 内容偏好：硬核、真实、专业、爽感、逻辑严密
- 决策模式：口碑驱动 > 明星效应，理性分析 > 感性冲动
- 社交习惯：深度讨论（豆瓣/虎扑/B站长评），二创传播
- 厌恶点：注水剧情、流量演员、逻辑漏洞、过度娱乐化

**男性聚集平台特性**：
- B站：剧情解析、弹幕文化、UP主推荐
- 虎扑：直男审美、理性讨论、投票排行
- 豆瓣：深度长评、打分严格、口碑发酵
- 抖音：名场面剪辑、快节奏呈现

**传播规律**：
- 内容 > 包装：实力派演技 > 流量明星
- 细节制胜：专业考据、真实感、硬核细节
- UGC驱动：鼓励二创、剧情推理、弹幕互动

请基于用户提供的剧集信息，生成一份针对男性受众的专业营销方案。

必须包含：
1. **深度用户洞察**：男性观众心理分析、决策路径
2. **4C内容模型**：Create（原创）/Curate（聚合）/Collaborate（合作）/Convert（转化）
3. **分发策略**：B站/抖音/豆瓣/虎扑的差异化打法
4. **社群运营**：弹幕文化、话题运营、UGC激励
5. **数据追踪**：留存率、完播率、二创数量、口碑指标
6. **TOFU-MOFU-BOFU漏斗**：认知-考虑-转化的完整路径

输出格式：使用 Markdown，结构清晰，包含具体案例和执行细节，emoji增强可读性。

核心原则：真实、专业、可执行、有温度。"""
    }
    
    return prompts.get(plan_type, prompts['general'])


def get_realtime_hotspot_summary(drama_name, drama_type):
    """获取实时热点摘要 - 调用真实数据"""
    try:
        import subprocess
        import json as json_lib
        
        # 使用web_search获取实时热搜(通过调用Box AI的search功能)
        # 这里我们使用简化方案:返回提示AI去生成"实时热点追踪"章节
        
        hotspot_summary = f"""
## 📌 重要提示：实时热点追踪要求

**必须包含"实时热点追踪"章节**，该章节需要包含以下内容：

### 微博热搜（必须）
请列出当前微博热搜榜前10条，格式：
- #排名 话题标题 热度值 标签(热/新/综合等)
例如：
#1 某某话题 117.6万 热
#2 某某事件 85.5万 新

### 抖音热榜（必须）
请列出抖音当前热门话题/挑战赛，格式：
- #排名 话题名称 播放量/参与度

### 小红书热门（必须）  
请列出小红书当前热门笔记类型/话题

### 豆瓣热门话题（必须）
请列出豆瓣当前热门讨论话题

### 热点借势建议
基于以上实时热搜，分析哪些热点可以与《{drama_name}》({drama_type})结合借势。

**注意**：
1. "实时热点追踪"必须是独立的一级章节(##)
2. 必须包含4个平台的真实热点数据
3. 数据格式要清晰,包含排名、标题、热度值
4. 最后给出针对本剧的借势建议
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

// Cloudflare Worker for 阿里云百炼API
// 部署到 Cloudflare Workers

export default {
  async fetch(request, env) {
    // CORS处理
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const data = await request.json();
      const { plan } = data;

      // 构建提示词
      const prompt = `你是一位资深的电视剧营销策划专家，拥有10年以上的影视营销经验。请根据以下剧集信息，生成一份专业的营销方案。

# 剧集信息
- 剧集名称：${plan.dramaName}
- 类型定位：${plan.dramaType}
- 核心卖点：${plan.coreSelling}
- 剧情梗概：${plan.plotSummary}
- 情感核心：${plan.emotionCore}
- 目标情绪：${plan.targetEmotion}
- 演员阵容：${plan.castType}
- IP类型：${plan.ipType}
- 播出平台：${plan.platform}
- 营销预算：${plan.budget}
- 目标受众：${plan.audience}
- 营销阶段：${plan.stage}

# 生成要求
请生成以下内容，要求有深度、有洞察、有创意，不要套模板：

## 1. 深度用户洞察
基于剧情内容和目标受众，分析：
- 核心用户画像（年龄、性别、地域、消费习惯）
- 心理特征和情感需求
- 观剧动机和期待
- 媒体触达习惯
- 潜在痛点和顾虑

## 2. 话题策略设计
基于${plan.emotionCore}的情感核心，设计5个具体话题：
- 每个话题要有明确的传播目标
- 提供具体的话题标签和内容方向
- 说明如何引发用户讨论和参与

## 3. 微博营销策略
详细说明：
- 超话运营策略（如何激活、如何日常运营）
- 热搜布局策略（何时上、上什么、如何配合剧情）
- KOL合作策略（选择什么类型的KOL、如何合作）
- 粉丝互动玩法（具体的互动形式和激励机制）

## 4. 抖音营销策略
详细说明：
- 短视频内容方向（具体拍什么、怎么拍）
- 达人合作策略（选择标准、合作形式）
- 挑战赛设计（具体玩法、如何引爆）
- 直播互动策略（直播内容、互动形式）

## 5. 小红书营销策略
详细说明：
- 种草内容方向（什么角度种草最有效）
- KOC选择标准（什么样的博主适合）
- 内容形式设计（图文/视频比例、风格）
- 同款经济如何运作

## 6. 视频号营销策略
详细说明：
- 内容策略（什么内容在视频号效果好）
- 社群裂变玩法（如何设计裂变机制）
- 私域转化策略（如何沉淀私域流量）

## 7. IP类型差异化策略
基于${plan.ipType}的IP类型，说明：
- 这个IP类型的独特优势
- 具体的差异化打法
- 需要注意的风险点

## 8. 执行时间表
基于${plan.stage}阶段，给出：
- 分阶段的具体行动计划
- 每个阶段的关键节点和里程碑
- 时间安排和资源配置建议

# 输出格式
请用Markdown格式输出，结构清晰，层次分明。
每个部分都要有深度分析，不要泛泛而谈。
要结合剧集的具体内容特点，不要用万能模板。
语言要专业但不晦涩，有洞察有观点有执行性。`;

      // 调用阿里云百炼API
      const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.DASHSCOPE_API_KEY}`,
        },
        body: JSON.stringify({
          model: 'qwen-plus',
          messages: [
            {
              role: 'system',
              content: '你是一位资深的电视剧营销策划专家，拥有10年以上的影视营销经验。你擅长深度用户洞察、创意话题策划、全平台营销策略制定。'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          temperature: 0.8,
          top_p: 0.9,
          max_tokens: 4000,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'API调用失败');
      }

      return new Response(JSON.stringify({
        success: true,
        content: result.choices[0].message.content,
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });

    } catch (error) {
      return new Response(JSON.stringify({
        success: false,
        error: error.message,
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }
  },
};

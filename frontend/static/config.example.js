/**
 * 高德地图配置模板
 *
 * 使用方式：
 *   1. 复制本文件为同目录下的 config.js
 *   2. 前往 https://lbs.amap.com/ 申请「Web端 (JS API)」类型的 Key
 *   3. 填入下方对应字段后保存并刷新页面
 *
 * config.js 已被 .gitignore 排除，不会被提交到公开仓库，
 * 请勿直接把 Key 写进 index.html 等入库文件。
 */

window.AMAP_CONFIG = {
    // 高德开放平台 Web端 (JS API) Key
    key: 'YOUR_AMAP_KEY_HERE',

    // 若申请 Key 时选择了「安全密钥」校验方式，需同时填写此项；否则留空即可
    securityJsCode: '',

    // 后端服务地址（需与 backend/app.py 实际监听地址一致）
    backendUrl: 'http://localhost:5000'
};

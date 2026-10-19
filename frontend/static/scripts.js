/**
 * 城市功能区智能分析平台 —— 前端交互逻辑
 *
 * 由 static/config.example.js 复制出的 config.js 提供
 *   window.AMAP_CONFIG.key / securityJsCode / backendUrl
 *
 * 入口约定：地图脚本加载完成后，index.html 会调用 window.initAMapApp()。
 */

// 功能区类别 -> 标注配色（需与 index.html 图例保持一致）
var TYPE_COLOR = {
    '商业区': '#FF4B4B',
    '居民区': '#4B8BFF',
    '工业区': '#FFB84B',
    '绿地/公园': '#4BFF4B'
};

var DEFAULT_COLOR = '#888888';

// 地图实例，未成功初始化时为 null
var mapInstance = null;
var markers = [];

/** 读取配置中的后端地址，缺省回落到本地默认端口 */
function getBackendUrl() {
    var cfg = window.AMAP_CONFIG || {};
    return cfg.backendUrl || 'http://localhost:5000';
}

/** HTML 转义，避免把后端返回的文本直接当 HTML 解析 */
function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function getTypeColor(type) {
    return TYPE_COLOR[type] || DEFAULT_COLOR;
}

// ------------------------------------------------------------------ 地图


/** 初始化高德地图与示例标注。地图不可用时静默降级，不影响图像分析功能。 */
function initMap() {
    if (typeof AMap === 'undefined') {
        console.warn('AMap 未加载，跳过地图初始化');
        return null;
    }

    var map = new AMap.Map('container', {
        viewMode: '3D',
        zoom: 3,
        center: [116.397428, 39.90923],
        pitch: 30,
        rotation: 0,
        mapStyle: 'amap://styles/dark',
        showLabel: true,
        layers: [new AMap.TileLayer.Satellite()],
        features: ['bg', 'road', 'building']
    });

    map.on('complete', function () {
        map.addControl(new AMap.Scale());
        map.addControl(new AMap.ToolBar({ position: 'LT' }));
        map.addControl(new AMap.ControlBar({ position: 'RT' }));
    });

    return map;
}

/** 示例点位，用于展示各功能区分布 */
var DEMO_POINTS = [
    { lnglat: [116.404, 39.915], name: '天安门广场', type: '绿地/公园' },
    { lnglat: [116.484, 39.923], name: '北京CBD', type: '商业区' },
    { lnglat: [116.319, 39.984], name: '中关村', type: '商业区' },
    { lnglat: [116.354, 39.874], name: '丰台科技园', type: '工业区' },
    { lnglat: [121.473, 31.230], name: '上海陆家嘴', type: '商业区' },
    { lnglat: [113.264, 23.129], name: '广州珠江新城', type: '商业区' },
    { lnglat: [114.057, 22.543], name: '深圳福田CBD', type: '商业区' }
];

function addMarker(position, title, type, labelText, size, iconUrl) {
    if (!mapInstance) { return null; }

    var marker = new AMap.Marker({
        position: position,
        title: title,
        icon: new AMap.Icon({
            size: new AMap.Size(size, size),
            image: iconUrl,
            imageSize: new AMap.Size(size, size)
        }),
        label: {
            content: '<div style="background:' + getTypeColor(type) +
                     '; color:white; padding:4px 8px; border-radius:12px; font-size:12px;">' +
                     escapeHtml(labelText) + '</div>',
            offset: new AMap.Pixel(10, -20)
        }
    });

    mapInstance.add(marker);
    markers.push(marker);
    return marker;
}

function addDemoMarkers() {
    DEMO_POINTS.forEach(function (point) {
        addMarker(
            point.lnglat,
            point.name,
            point.type,
            point.type,
            24,
            'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png'
        );
    });
}

// ------------------------------------------------------------ 上传与分析


function bindUploadUI() {
    var uploadBtn = document.querySelector('.upload-btn');
    var fileInput = document.getElementById('imageUpload');

    // label 的 for 属性已关联 input，这里补一次点击代理以防样式层遮挡
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', function (event) {
            if (event.target !== fileInput) {
                fileInput.click();
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', function (event) {
            var file = event.target.files && event.target.files[0];
            if (file && uploadBtn) {
                uploadBtn.textContent = '📤 ' + file.name;
            }
        });
    }
}

function bindAnalyzeButton() {
    var analyzeBtn = document.getElementById('analyzeBtn');
    var fileInput = document.getElementById('imageUpload');
    var resultBox = document.getElementById('result');

    if (!analyzeBtn || !fileInput || !resultBox) { return; }

    analyzeBtn.addEventListener('click', function () {
        var file = fileInput.files && fileInput.files[0];

        if (!file) {
            alert('请先选择一张卫星图像切片');
            return;
        }

        var formData = new FormData();
        formData.append('image', file);

        resultBox.innerHTML = '<p>正在分析中，请稍候...</p>';
        analyzeBtn.disabled = true;

        fetch(getBackendUrl() + '/predict', {
            method: 'POST',
            body: formData
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                if (data.error) {
                    resultBox.innerHTML = '<p style="color:red;">错误: ' +
                        escapeHtml(data.error) + '</p>';
                    return;
                }

                // 后端返回的 category 不在已知列表时给出提示，避免静默取到 undefined 配色
                if (Object.prototype.hasOwnProperty.call(TYPE_COLOR, data.class) === false) {
                    resultBox.innerHTML =
                        '<p style="color:#FFA500;">⚠️ 未知类别: ' +
                        escapeHtml(data.class) + '</p>';
                    return;
                }

                var confidencePercent = (Number(data.confidence) * 100).toFixed(1);
                resultBox.innerHTML =
                    '<p><strong>功能区类别：</strong>' + escapeHtml(data.class) + '</p>' +
                    '<p><strong>置信度：</strong>' + confidencePercent + '%</p>' +
                    '<p><small>分析时间：' +
                    new Date().toLocaleTimeString() + '</small></p>';

                if (mapInstance) {
                    var center = mapInstance.getCenter();
                    addMarker(
                        [center.lng + (Math.random() - 0.5) * 0.5,
                         center.lat + (Math.random() - 0.5) * 0.5],
                        '分析结果: ' + data.class,
                        data.class,
                        data.class + ' ' + confidencePercent + '%',
                        30,
                        'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png'
                    );
                    mapInstance.setZoom(14);
                }
            })
            .catch(function (error) {
                console.error('Error:', error);
                resultBox.innerHTML =
                    '<p style="color:red;">分析失败，请检查后端服务是否启动（' +
                    escapeHtml(getBackendUrl()) + '）。</p>';
            })
            .then(function () {
                analyzeBtn.disabled = false;
            });
    });
}

// ------------------------------------------------------------------ 入口


/**
 * 地图脚本就绪后由 index.html 调用。
 * 拆成「地图」与「交互」两条独立路径：即使地图不可用，图像分析仍可正常使用。
 */
function initAMapApp() {
    mapInstance = initMap();
    if (mapInstance) {
        addDemoMarkers();
    }

    bindUploadUI();
    bindAnalyzeButton();
}

window.initAMapApp = initAMapApp;

// 兜底：若 config.js 未提供 Key，index.html 不会加载地图脚本，
// 此时仍需完成 UI 事件绑定，保证上传与分析功能可用。
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        if (window.__AMAP_CONFIG_MISSING__) { initAMapApp(); }
    });
} else if (window.__AMAP_CONFIG_MISSING__) {
    initAMapApp();
}

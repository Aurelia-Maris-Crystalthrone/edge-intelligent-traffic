// 等待高德地图 API 完全加载
function initMap() {
    // 初始化地图实例
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

    // 在地图加载完成后添加控件（确保 AMap 控件类已就绪）
    map.on('complete', function() {
        // 添加比例尺控件
        map.addControl(new AMap.Scale());
        
        // 添加工具条（缩放、旋转等）
        map.addControl(new AMap.ToolBar({
            position: 'LT'
        }));
        
        // 添加罗盘/控制栏
        map.addControl(new AMap.ControlBar({
            position: 'RT'
        }));
    });

    // 存储标记点
    var markers = [];

    // 示例点（展示用）
    var demoPoints = [
        { lnglat: [116.404, 39.915], name: '天安门广场', type: '绿地/公园' },
        { lnglat: [116.484, 39.923], name: '北京CBD', type: '商业区' },
        { lnglat: [116.319, 39.984], name: '中关村', type: '商业区' },
        { lnglat: [116.354, 39.874], name: '丰台科技园', type: '工业区' },
        { lnglat: [121.473, 31.230], name: '上海陆家嘴', type: '商业区' },
        { lnglat: [113.264, 23.129], name: '广州珠江新城', type: '商业区' },
        { lnglat: [114.057, 22.543], name: '深圳福田CBD', type: '商业区' }
    ];

    var typeColor = {
        '商业区': '#FF4B4B',
        '居民区': '#4B8BFF',
        '工业区': '#FFB84B',
        '绿地/公园': '#4BFF4B'
    };

    // 添加示例标注
    demoPoints.forEach(function(point) {
        var marker = new AMap.Marker({
            position: point.lnglat,
            title: point.name,
            icon: new AMap.Icon({
                size: new AMap.Size(24, 24),
                image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
                imageSize: new AMap.Size(24, 24)
            }),
            label: {
                content: '<div style="background:' + typeColor[point.type] + '; color:white; padding:4px 8px; border-radius:12px; font-size:12px;">' + point.type + '</div>',
                offset: new AMap.Pixel(10, -20)
            }
        });
        map.add(marker);
        markers.push(marker);
    });

    // 上传图片功能
    document.getElementById('imageUpload').addEventListener('change', function(e) {
        var file = e.target.files[0];
        if (file) {
            document.querySelector('.upload-btn').textContent = file.name;
        }
    });

    document.querySelector('.upload-btn').addEventListener('click', function() {
        document.getElementById('imageUpload').click();
    });

    document.getElementById('analyzeBtn').addEventListener('click', function() {
        var fileInput = document.getElementById('imageUpload');
        var file = fileInput.files[0];
        
        if (!file) {
            alert('请先选择一张卫星图像切片');
            return;
        }
        
        var resultBox = document.getElementById('result');
        resultBox.innerHTML = '<p>正在分析中，请稍候...</p>';
        
        var formData = new FormData();
        formData.append('image', file);
        
        fetch('http://localhost:5000/predict', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(function(data) {
            if (data.error) {
                resultBox.innerHTML = '<p style="color:red;">错误: ' + data.error + '</p>';
                return;
            }
            
            var confidencePercent = (data.confidence * 100).toFixed(1);
            resultBox.innerHTML = `
                <p><strong>功能区类别：</strong>${data.class}</p>
                <p><strong>置信度：</strong>${confidencePercent}%</p>
                <p><small>分析时间：${new Date().toLocaleTimeString()}</small></p>
            `;
            
            // 在当前视图中心附近添加标记
            var center = map.getCenter();
            var marker = new AMap.Marker({
                position: [center.lng + (Math.random() - 0.5) * 0.5, center.lat + (Math.random() - 0.5) * 0.5],
                title: '分析结果: ' + data.class,
                icon: new AMap.Icon({
                    size: new AMap.Size(30, 30),
                    image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
                    imageSize: new AMap.Size(30, 30)
                }),
                label: {
                    content: '<div style="background:' + typeColor[data.class] + '; color:white; padding:4px 8px; border-radius:12px; font-size:12px;">' + data.class + ' ' + confidencePercent + '%</div>',
                    offset: new AMap.Pixel(15, -25)
                }
            });
            map.add(marker);
            markers.push(marker);
            
            map.setCenter(marker.getPosition());
            map.setZoom(14);
        })
        .catch(function(error) {
            console.error('Error:', error);
            resultBox.innerHTML = '<p style="color:red;">分析失败，请检查后端服务是否启动。</p>';
        });
    });
}

// 确保高德 API 加载完成后再初始化地图
if (typeof AMap !== 'undefined') {
    initMap();
} else {
    window.onload = initMap;
}
document.addEventListener('DOMContentLoaded', () => { fetchData(); });

async function fetchData() {
    const btn = document.getElementById('refresh-btn');
    const icon = btn.querySelector('i');
    const loading = document.getElementById('loading');
    const content = document.getElementById('dashboard-content');
    
    icon.classList.add('rotating');
    if(content.style.display === 'none') loading.style.display = 'flex';

    try {
        const response = await fetch('/api/data');
        const result = await response.json();
        
        if (result.success) {
            updateDashboard(result.data);
            loading.style.display = 'none';
            content.style.display = 'block';
        } else {
            alert('データの取得に失敗しました: ' + result.error);
            loading.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('ネットワークエラーが発生しました。');
        loading.style.display = 'none';
    } finally {
        icon.classList.remove('rotating');
    }
}

function updateDashboard(data) {
    document.getElementById('time-updated').textContent = data.last_updated;
    document.getElementById('chart-img').src = data.image_url;
    
    const analysisList = document.getElementById('analysis-list');
    analysisList.innerHTML = '';
    data.analysis.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        analysisList.appendChild(li);
    });
    
    const cardsGrid = document.getElementById('stats-cards');
    cardsGrid.innerHTML = '';
    
    data.stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card glass-panel';
        
        const isUp = stat.return_1y >= 0;
        const returnClass = isUp ? 'return-up' : 'return-down';
        const iconClass = isUp ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';
        const sign = isUp ? '+' : '';
        const formattedPrice = stat.current_price > 1000 
            ? stat.current_price.toLocaleString(undefined, {maximumFractionDigits: 0})
            : stat.current_price.toLocaleString(undefined, {maximumFractionDigits: 2});
            
        card.innerHTML = `
            <div class="stat-name">${stat.name}</div>
            <div class="stat-price">${formattedPrice}</div>
            <div class="stat-return ${returnClass}">
                <i class="fa-solid ${iconClass}"></i> ${sign}${stat.return_1y.toFixed(2)}%
            </div>
            <div style="font-size: 0.8rem; color: #9da3b4; margin-top: 5px;">高値圏割合: ${stat.position_1y.toFixed(1)}%</div>
            <div class="position-bar-bg">
                <div class="position-bar-fill" style="width: ${Math.max(0, Math.min(100, stat.position_1y))}%"></div>
            </div>
        `;
        cardsGrid.appendChild(card);
    });
}

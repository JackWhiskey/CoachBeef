import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { DashboardData } from '../utils/entities';

export default function DashboardPanel({ selectedActivityId }: { selectedActivityId: number | null }) {
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(false);

    const generateDashboard = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/dashboard/generate?activity_id=${selectedActivityId}`, {
                method: 'POST'
            });
            
            let data = await res.json();
            
            if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            
            setDashboard(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <button onClick={generateDashboard} disabled={!selectedActivityId || loading}>
                {loading ? "Crunching Numbers..." : "Generate AI Dashboard"}
            </button>

            {dashboard && (
                <div style={{ marginTop: '20px' }}>
                    <p style={{ fontSize: '1.1rem', marginBottom: '20px' }}>
                        {dashboard.summary_text}
                    </p>

                    {/* Loop through the charts OpenAI generated and render them! */}
                    {dashboard.charts.map((chartOption, index) => {
                        const finalEChartsConfig = {
                            ...chartOption,
                            tooltip: { trigger: 'axis' }
                        };

                        return (
                            <div key={index} style={{ marginBottom: '40px', backgroundColor: '#fff', padding: '20px', borderRadius: '12px', border: '1px solid #eee' }}>
                                <ReactECharts 
                                    option={finalEChartsConfig} 
                                    style={{ height: '400px', width: '100%' }} 
                                    opts={{ renderer: 'svg' }}
                                />
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
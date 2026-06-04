from pydantic import BaseModel

# 1. Strictly define the Title
class ChartTitle(BaseModel):
    text: str

# 2. Strictly define an Axis (X or Y)
class ChartAxis(BaseModel):
    type: str # e.g., 'value' or 'category'
    # Use an empty list if the axis type is 'value'
    data: list[str] 

# 3. Strictly define the Series
class ChartSeries(BaseModel):
    name: str
    type: str # e.g., 'line', 'bar'
    data: list[float]

# 4. Assemble the ECharts Option without any open 'dict' types!
class EChartOption(BaseModel):
    title: ChartTitle
    xAxis: ChartAxis
    yAxis: ChartAxis
    series: list[ChartSeries]

# 5. The final dashboard payload
class DashboardModel(BaseModel):
    summary_text: str
    charts: list[EChartOption]

class ChartIdea(BaseModel):
    title: str
    reasoning: str # Forcing the LLM to explain *why* makes the results much smarter!
    required_data: list[str] # e.g., ["lap_paces", "average_heartrate"]

class DashboardPlan(BaseModel):
    coach_insight: str
    recommended_charts: list[ChartIdea]
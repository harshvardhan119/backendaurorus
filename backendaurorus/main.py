from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods including POST, OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# Define the structure of the incoming request using Pydantic models
class InputData(BaseModel):
    state: str
    population_size: int
    gpcd: float
    plant_factor: float
    precipitation: float
    cultivated_land: float
    demographic_shift: float
    curr_year: int

@app.post("/calculate")
async def calculate(data: InputData):
    # Function to calculate water requirements
    def calculate_requirement(curr_year, year, population_size, gpcd, plant_factor, precipitation, cultivated_land, demographic_shift):
        GALLONS_TO_CUBIC_METERS = 0.00378541
        CUBIC_METERS_TO_BMC = 1e-9

        def convert_to_bmc(value_in_gallons):
            return value_in_gallons * GALLONS_TO_CUBIC_METERS * CUBIC_METERS_TO_BMC*100

        def calculate_baseline(population_size, gpcd, plant_factor):
            baseline_gallons = population_size * gpcd * plant_factor
            return convert_to_bmc(baseline_gallons)*100

        def calculate_predicted(baseline_bmc, demographic_shift, precipitation):
            return (baseline_bmc * (1 + demographic_shift / 100) * (1 - precipitation / 100))

        def calculate_actual(predicted_bmc, cultivated_land):
            return predicted_bmc * (1 + cultivated_land / 100)
        
        baseline_bmc = calculate_baseline(population_size, gpcd, plant_factor)
        predicted_bmc = calculate_predicted(baseline_bmc, demographic_shift, precipitation)
        actual_bmc = calculate_actual(predicted_bmc, cultivated_land)
        
        return {
            'year': curr_year + year,
            'baseline': baseline_bmc,
            'predicted_requirement': predicted_bmc,
            'actual_requirement': actual_bmc
        }

    years = list(range(0, 6))
    results = []

    for year in years:
        updated_population = data.population_size + (2500 * year)
        updated_precipitation = data.precipitation * (1 - 0.05 * year)
        
        result = calculate_requirement(data.curr_year, year, updated_population, data.gpcd, data.plant_factor, updated_precipitation, data.cultivated_land, data.demographic_shift)
        results.append(result)

    response = {
        'state': data.state,
        'parameters': results
    }

    return response

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)





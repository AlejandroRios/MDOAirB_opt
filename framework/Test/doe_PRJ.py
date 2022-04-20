'''

'''

from framework.Database.Aircrafts.baseline_aircraft_parameters import initialize_aircraft_parameters
vehicle = initialize_aircraft_parameters()
#=========================================

# SETUP

# Define history list
# Define design function
from framework.Optimization.objective_function import objective_function

# Give number of input variables

n_inputs = 16

# Lower and upeer bounds of each input variable
#     0   | 1   | 2   |  3     |   4    |   5      | 6     | 7     |  8     |   9   | 10    | 11    |   12     | 13    | 14          |  15

lb = []
ub = []

    fan_pressure_ratio = engine['fan_pressure_ratio']
    compressor_pressure_ratio = engine['compressor_pressure_ratio']
    bypass_ratio = engine['bypass']
    fan_diameter = engine['fan_diameter']
    turbine_inlet_temperature = engine['turbine_inlet_temperature']
# Desired number of samples
n_samples = 200

# Sampling type
#sampling_type = 'real_random'
sampling_type = 'int_lhs'

# Plot type (0-simple, 1-complete)
plot_type = 1
#=========================================

# EXECUTION

# Set random seed to make results repeatable
np.random.seed(123)

# Initialize sampler
sampling = get_sampling(sampling_type)

# Draw samples
X = sample(sampling, n_samples, n_inputs)



vehicle = initialize_aircraft_parameters()

# Samples are originally between 0 and 1,
# so we need to scale them to the desired interval
for ii in range(n_inputs):
    X[:,ii] = lb[ii] + (ub[ii] - lb[ii])*X[:,ii]

# Execute all cases and store outputs
y1_samples = []
# y2_samples = []
for ii in range(n_samples):

    # Evaluate sample
    y1= objective_function(vehicle,X[ii,:])

    # Store the relevant information
    y1_samples.append(y1)
    # y2_samples.append(y2)

# Create a pandas dataframe with all the information
df = pd.DataFrame({'x1' : X[:,0],
                   'x2' : X[:,1],
                   'x3' : X[:,2],
                   'x4' : X[:,3],
                   'x5' : X[:,4],
                   'x6' : X[:,5],
                   'x7' : X[:,6],
                   'x8' : X[:,7],
                   'x9' : X[:,8],
                   'x10' : X[:,9],
                   'x11' : X[:,10],
                   'x12' : X[:,11],
                   'x13' :X[:,12],
                   'x14' :X[:,13],
                   'x15' :X[:,14],
                   'x16' :X[:,15],
                   'y1' : y1_samples})
# Plot the correlation matrix
sns.set(style='white', font_scale=1.4)

if plot_type == 0:

    # Simple plot
    fig = sns.pairplot(df,corner=True)

elif plot_type == 1:

    # Complete plot
    # based on: https://stackoverflow.com/questions/48139899/correlation-matrix-plot-with-coefficients-on-one-side-scatterplots-on-another
    fig = sns.PairGrid(df, diag_sharey=False)
    fig.map_lower(sns.regplot, lowess=True, line_kws={'color': 'black'})
    fig.map_diag(sns.histplot)
    fig.map_upper(corrdot)

# Plot window
plt.tight_layout()
plt.show()

plt.savefig('doe.pdf', dpi=None, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format='pdf',
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)
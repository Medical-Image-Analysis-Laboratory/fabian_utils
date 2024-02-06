import numpy as np
import random
import matplotlib.pyplot as plt

def generate_subranges(start, end, num_subranges):
    
    # Generate logarithmically spaced points between 0 and 1
    points = np.logspace(0,1, num_subranges, base=10,endpoint=False)-1
    
    # Scale points to fit the desired range
    scaled_points = start + (end - start) * points /10
    scaled_points = np.append(scaled_points,end)

    # Round the scaled points to integers
    rounded_points = np.round(scaled_points).astype(int)

    # Create subranges
    subranges = [(rounded_points[i-1], rounded_points[i]) for i in range(1, len(rounded_points))]

    return subranges

def select_subrange(subranges,target_mean,flat_factor=0.2):

    # Calculate means of the subranges
    subrange_means = [(start + end) / 2 for start, end in subranges]

    # Calculate distances between the means and the target mean
    distances = np.abs(np.array(subrange_means) - target_mean)

    # Calculate probabilities based on distances
    probabilities = 1 / distances
    probabilities = probabilities**flat_factor
    probabilities /= probabilities.sum()

    # Select one subrange randomly with uniform weighting
    return np.random.choice(len(subranges), p=probabilities), np.round(probabilities,2)


""" # Example: Splitting the range 1-2000 into 9 subranges
start_range = 0
end_range = 2000
num_subranges = 4
tissues = ["wm", "gm", "csf"]
target_means = [285, 181, 2000]
flat_factors = [0.2,0.2,0.6]

subranges = generate_subranges(start_range, end_range, num_subranges)
#selected_subrange, probabilities = select_subrange(subranges, 285)

for i, subrange in enumerate(subranges):
    print(f"Subrange {i + 1}: {subrange[0]} - {subrange[1]}")

for tissue, target_mean, flat_factor in zip(tissues, target_means, flat_factors):

    subranges = generate_subranges(start_range, end_range, num_subranges)
    selected_subrange, probabilities = select_subrange(subranges, target_mean,flat_factor)

    print(f"{tissue.upper()} Subranges probabilities: {probabilities}")
    print(f"{tissue.upper()} Selected subrange: {subranges[selected_subrange]}")
    random_value = np.random.uniform(subranges[selected_subrange][0], subranges[selected_subrange][1])
    print(f"{tissue.upper()} Selected value {tissue}: {random_value}") 
 """

def inverse_cdf(u, a,b, alpha, beta, gamma):
    """
    Inverse CDF that maps a uniformly distributed vector of values between 0 and 1 to a vector of values
    that are T2 values that will follow the distribution U(a,b) after being
    transformed through the model beta*exp(-alpha/T2)-gamma.
    """
    assert max(u) <= 1 and min(u) >= 0, "u must be between 0 and 1"

    return -alpha/(np.log(((b-a)*u+a-gamma)/beta))



# Example usage to generate a random value within the range [0, 2000]
a = 100
b = 2000
alpha = 300
beta = 2000
gamma = 100
bin_size= 100
# Generate a random value u between 0 and 1
random_u = np.random.rand(100000)

# Use inverse_cdf to get the corresponding value in the distribution
random_value = np.round(inverse_cdf(random_u, a, b, alpha, beta, gamma),2)
print("uniform values", np.round(random_u,2))
print("Generated Random Value:", random_value)

hist_array1, bins_array1 = np.histogram(random_value, bins=np.arange(100, 2000 + bin_size, bin_size),density=True)
plt.bar(bins_array1[:-1],hist_array1, width=bin_size, alpha=0.65,color='violet')
plt.show()

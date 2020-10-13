# %%
"""
Tutorial 3: Aggregator
======================

In the previous tutorial, we fitted 3 `Datasets` with an identical `Phase`, outputting the results of each to a unique
folder on our hard disk.

However, lets use the `Aggregator` to load the `Result`'s and manipulate / plot them using our Jupyter notebook. The
API for using `Result`'s follow closely tutorial 1 of this chapter.
"""

# %%
#%matplotlib inline

from autoconf import conf
import autofit as af
from howtofit.chapter_2_results import src as htf

import numpy as np
import os

workspace_path = os.environ["WORKSPACE"]
print("Workspace Path: ", workspace_path)

# %%
"""
Setup the configs as we did in the previous tutorial, as well as the output folder for our `NonLinearSearch`.
"""

# %%
conf.instance = conf.Config(
    config_path=f"config",
    output_path=f"output/chapter_2",
)

# %%
"""
To load the results of the previous tutorial into the `Aggregator`, we simply point the `Aggregator` class to the path 
of the results we want it to load.
"""

# %%
output_path = f"output/chapter_2/aggregator"

agg = af.Aggregator(directory=str(output_path))

# %%
"""
To begin, let me quickly explain what a generator is in Python, for those unaware. A generator is an object that 
iterates over a function when it is called. The `Aggregator` creates all objects as generators, rather than lists, or 
dictionaries, or whatever.

Why? Because lists and dictionaries store every entry in memory simultaneously. If you fit many `Dataset`s, you`ll 
have lots of results and therefore use a lot of memory. This will crash your laptop! On the other hand, a generator 
only stores the object in memory when it runs the function; it is free to overwrite it afterwards. Thus, your laptop 
won't crash!

There are two things to bare in mind with generators:

 1) A generator has no length, thus to determine how many entries of data it corresponds to you first must turn it to a 
    list.

 2) Once we use a generator, we cannot use it again and we'll need to remake it. For this reason, we typically avoid 
    storing the generator as a variable and instead use the `Aggregator` to create them on use.

We can now create a `Samples` generator of every fit. This creates instances of the `Samples` class we manipulated in
tutorial 1, which with the `Aggregator` now acts as an interface between the results of the non-linear fit on your 
hard-disk and Python.
"""

# %%
samples_gen = agg.values("samples")

# %%
"""
When we print this list of outputs you should see over 3 different `NestSamples` instances, corresponding to the 3
model-fits we performed in the previous tutorial.
"""

# %%
print("Emcee Samples:\n")
print(samples_gen)
print("Total Samples Objects = ", len(list(samples_gen)), "\n")


# %%
"""
We've encountered the `Samples` class in previous tutorials. As we saw in tutorial 1, the `Samples` class contains all 
the accepted parameter samples of the `NonLinearSearch`, which is a list of lists where:

 - The outer list is the size of the total number of samples.
 - The inner list is the size of the number of free parameters in the fit.

With the `Aggregator` we can now get information on the `Samples` of all 3 model-fits, as opposed to just 1 fit using 
its `Result` object.
"""

# %%
for samples in agg.values("samples"):
    print("All parameters of the very first sample")
    print(samples.parameters[0])
    print("The tenth sample`s third parameter")
    print(samples.parameters[9][2])
    print()

# %%
"""
We can use the `Aggregator` to get information on the `log_likelihoods`, log_priors`, `weights`, etc. of every fit.
"""

# %%
for samples in agg.values("samples"):
    print("log(likelihood), log(prior), log(posterior) and weight of the tenth sample.")
    print(samples.log_likelihoods[9])
    print(samples.log_priors[9])
    print(samples.log_posteriors[9])
    print(samples.weights[9])
    print()

# %%
"""
We can use the `Sample`'s to create a list of the `max_log_likelihood_vector` of each fit to our three images.
"""

# %%
vector = [samps.max_log_likelihood_vector for samps in agg.values("samples")]
print("Maximum Log Likelihood Parameter Lists:\n")
print(vector, "\n")

# %%
"""
As discussed in tutorial 1, using vectors isn't too much use, as we can`t be sure which values correspond to which 
parameters.

We can use the `Aggregator` to create the `max_log_likelihood_instance` of every fit.
"""

# %%
instances = [samps.max_log_likelihood_instance for samps in agg.values("samples")]
print("Maximum Log Likelihood Model Instances:\n")
print(instances, "\n")

# %%
"""
The model instance contains all the model components of our fit which for the fits above was a single `Gaussian`
profile (the word `gaussian` comes from what we called it in the `CollectionPriorModel` above).
"""

# %%
print(instances[0].profiles.gaussian)
print(instances[1].profiles.gaussian)
print(instances[2].profiles.gaussian)

# %%
"""
This, of course, gives us access to any individual parameter of our maximum log likelihood `instance`. Below, we see 
that the 3 `Gaussian`s were simulated using `sigma` values of 1.0, 5.0 and 10.0.
"""

# %%
print(instances[0].profiles.gaussian.sigma)
print(instances[1].profiles.gaussian.sigma)
print(instances[2].profiles.gaussian.sigma)

# %%
"""
We can also access the `median_pdf` model via the `Aggregator`, as we saw for the `Samples` object in tutorial 1.
"""

# %%
mp_vectors = [samps.median_pdf_vector for samps in agg.values("samples")]
mp_instances = [samps.median_pdf_instance for samps in agg.values("samples")]

print("Median PDF Model Parameter Lists:\n")
print(mp_vectors, "\n")
print("Most probable Model Instances:\n")
print(mp_instances, "\n")

# %%
"""
We can also print the `model_results` of all phases, which is string that summarizes every fit`s model providing
quick inspection of all results.
"""

# %%
results = agg.model_results
print("Model Results Summary:\n")
print(results, "\n")

# %%
"""
Lets end the tutorial with something more ambitious. Lets create a plot of the inferred `sigma` values vs `intensity` 
of each `Gaussian` profile, including error bars at $3\sigma$ confidence.
"""

# %%
import matplotlib.pyplot as plt

mp_instances = [samps.median_pdf_instance for samps in agg.values("samples")]
ue3_instances = [
    samp.error_instance_at_upper_sigma(sigma=3.0) for samp in agg.values("samples")
]
le3_instances = [
    samp.error_instance_at_lower_sigma(sigma=3.0) for samp in agg.values("samples")
]

mp_sigmas = [instance.profiles.gaussian.sigma for instance in mp_instances]
ue3_sigmas = [instance.profiles.gaussian.sigma for instance in ue3_instances]
le3_sigmas = [instance.profiles.gaussian.sigma for instance in le3_instances]
mp_intensitys = [instance.profiles.gaussian.sigma for instance in mp_instances]
ue3_intensitys = [instance.profiles.gaussian.sigma for instance in ue3_instances]
le3_intensitys = [instance.profiles.gaussian.intensity for instance in le3_instances]

plt.errorbar(
    x=mp_sigmas,
    y=mp_intensitys,
    marker=".",
    linestyle="",
    xerr=[le3_sigmas, ue3_sigmas],
    yerr=[le3_intensitys, ue3_intensitys],
)
plt.show()

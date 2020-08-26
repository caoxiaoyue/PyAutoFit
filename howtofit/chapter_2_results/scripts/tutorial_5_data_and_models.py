# %%
"""
Tutorial 5: Data and Models
===========================

Up to now, we've used used the _Aggregator_ to load and inspect the _Samples_ of 3 model-fits..

In this tutorial, we'll look at how the way we designed our source code makes it easy to use the _Aggregator_ to
inspect, interpret and plot the results of the model-fit, including refitting the best models to our data.
"""

# %%
#%matplotlib inline

from autoconf import conf
import autofit as af
from howtofit.chapter_2_results import src as htf

from pyprojroot import here

workspace_path = str(here())
print("Workspace Path: ", workspace_path)

# %%
"""
Setup the configs as we did in the previous tutorial, as well as the output folder for our non-linear search.
"""

# %%
conf.instance = conf.Config(
    config_path=f"{workspace_path}/howtofit/config",
    output_path=f"{workspace_path}/howtofit/output/chapter_2",
)

# %%
"""
To load these results with the _Aggregator_, we again point it to the path of the results we want it to inspect, with
our path straight to the _Aggregator_ results ensuring w don't need to filter our _Aggregator_ in this tutorial.
"""

# %%
output_path = f"{workspace_path}/howtofit/output/chapter_2/aggregator"
agg = af.Aggregator(directory=str(output_path))

# %%
"""
We can use the _Aggregator_ to load a generator of every fit's dataset, by changing the 'output' attribute to the 
'dataset' attribute at the end of the aggregator.

Note that in the source code for chapter 2, specifically in the 'phase.py' module, we specified that the the _Dataset_ 
object would be saved too hard-disk such that the _Aggregator_ can load it.
"""

# %%
dataset_gen = agg.values("dataset")
print("Datasets:")
print(list(dataset_gen), "\n")

# %%
"""
It is here the object-oriented design of our plot module comes into its own. We have the _Dataset_ objects loaded, 
meaning we can easily plot each _Dataset_ using the 'dataset_plot.py' module.
"""

# %%
for dataset in agg.values("dataset"):
    htf.plot.Dataset.data(dataset=dataset)

# %%
"""
The _Dataset_ names are available, either as part of the _Dataset_ or via the aggregator's dataset_names method.
"""

# %%
for dataset in agg.values("dataset"):
    print(dataset.name)

# %%
"""
The info dictionary we input into the pipeline is also available.
"""

# %%
for info in agg.values("info"):
    print(info)

# %%
"""
We can repeat the same trick to get the mask of every fit.
"""

# %%
mask_gen = agg.values("mask")
print("Masks:")
print(list(mask_gen), "\n")


# %%
"""
We're going to refit each dataset with the maximum log likelihood model-fit of each phase. To do this, we'll need 
each phase's masked dataset.

(If you are unsure what the 'zip' is doing below, it essentially combines the'datasets' and 'masks' lists in such
a way that we can iterate over the two simultaneously to create each MaskedDataset).

The _MaskedDataset_ may have been altered by the *data_trim_left* and *data_trim_right* custom phase settings. We can 
load the _SettingsPhase_ via the _Aggregator_ to use these settings when we create the _MaskedDataset_.
"""

# %%
dataset_gen = agg.values("dataset")
mask_gen = agg.values("mask")
settings_gen = agg.values("settings")

masked_datasets = [
    htf.MaskedDataset(
        dataset=dataset, mask=mask, settings=settings.settings_masked_dataset
    )
    for dataset, mask, settings in zip(dataset_gen, mask_gen, settings_gen)
]

# %%
"""
There is a problem with how we set up the _MaskedDataset_'s above, can you guess what it is?

We used lists! If we had fit a large sample of data, the above object would store the _MaskedDataset_ of all objects
simultaneously in memory on our hard-disk, likely crashing our laptop! To avoid this, we must write functions that
manipulate the _Aggregator_ generators as generators themselves. Below is an example function that performs the same
task as above.
"""

# %%
def masked_dataset_from_agg_obj(agg_obj):

    dataset = agg_obj.dataset
    mask = agg_obj.mask
    settings = agg_obj.settings

    return htf.MaskedDataset(
        dataset=dataset, mask=mask, settings=settings.settings_masked_dataset
    )


# %%
"""
To manipulate this function as a generator using the _Aggregator_, we apply it to the _Aggregator_'s map function.

The *masked_dataset_gen* below ensures that we avoid representing all _MaskeddDataset_'s simultaneously in memory.
"""

# %%
masked_dataset_gen = agg.map(func=masked_dataset_from_agg_obj)
print(list(masked_dataset_gen))

# %%
"""
Lets get the the maximum likelihood model instances, as we did in tutorial 3.
"""

# %%
instances = [samps.max_log_likelihood_instance for samps in agg.values("samples")]

# %%
"""
Okay, we want to inspect the fit of each maximum log likelihood model. To do this, we reperform each fit.

First, we need to create the model-data of every maximum log likelihood model instance. Lets begin by creating a list 
of profiles of every phase.
"""

# %%
profiles = [instance.profiles for instance in instances]

# %%
"""
We can use these to create the model data of each set of profiles (Which in this case is just 1 Gaussian, but had
we included more profiles in the model would consist of multiple _Gaussian_'s / _Exponential_'s).
"""

# %%
model_datas = [
    profile.gaussian.profile_from_xvalues(xvalues=dataset.xvalues)
    for profile, dataset in zip(profiles, agg.values("dataset"))
]

# %%
"""
And, as we did in tutorial 2, we can combine the _MaskedDataset_'s and model_datas in a _Fit_ object to create the
maximum likelihood fit of each phase!
"""

# %%
fits = [
    htf.FitDataset(masked_dataset=masked_dataset, model_data=model_data)
    for masked_dataset, model_data in zip(masked_datasets, model_datas)
]

# %%
"""
We can now plot different components of the fit (again benefiting from how we set up the 'fit_plots.py' module)!
"""

# %%
for fit in fits:
    htf.plot.FitDataset.residual_map(fit=fit)
    htf.plot.FitDataset.normalized_residual_map(fit=fit)
    htf.plot.FitDataset.chi_squared_map(fit=fit)

# %%
"""
Again, the code above does not use generators and could prove memory intensive for large datasets. Below is how we 
would perform the above task with generator functions, using the *masked_dataset_gen* above for the _MaskedDataset_.
"""

# %%
def model_data_from_agg_obj(agg_obj):

    xvalues = agg_obj.dataset.xvalues
    instance = agg_obj.samples.max_log_likelihood_instance
    profiles = instance.profiles

    return sum([profile.profile_from_xvalues(xvalues=xvalues) for profile in profiles])


def fit_from_agg_obj(agg_obj):

    masked_dataset = masked_dataset_from_agg_obj(agg_obj=agg_obj)
    model_data = model_data_from_agg_obj(agg_obj=agg_obj)

    return htf.FitDataset(masked_dataset=masked_dataset, model_data=model_data)


fit_gen = agg.map(func=fit_from_agg_obj)

for fit in fit_gen:
    htf.plot.FitDataset.residual_map(fit=fit)
    htf.plot.FitDataset.normalized_residual_map(fit=fit)
    htf.plot.FitDataset.chi_squared_map(fit=fit)

# %%
"""
Setting up the above objects (the masked_datasets, model datas, fits) was a bit of work. It wasn't too many lines of 
code, but for something our users will want to do many times it'd be nice to have a short cut to setting them up, right?

In the source code module 'aggregator.py' we've set up exactly such a short-cut. This module simply contains the 
generator functions above such that the generator can be created by passing the _Aggregator_. This provides us with 
convenience methods for quickly creating the _MaskedDataset_, model data and _Fit_'s using a single line of code:
"""

# %%

masked_dataset_gen = htf.agg.masked_dataset_generator_from_aggregator(aggregator=agg)
model_data_gen = htf.agg.model_data_generator_from_aggregator(aggregator=agg)
fit_gen = htf.agg.fit_generator_from_aggregator(aggregator=agg)

htf.plot.FitDataset.residual_map(fit=list(fit_gen)[0])

# %%
"""
The methods in 'aggregator.py' actually allow us to go one step further: they all us to create the _MaskedDataset_ and
_Fit_ objects using an input _SettingsMaskedDataset_. This means we can fit a _Dataset_ with a _Phase_ and then see how
the model-fits change if we set the _Dataset_ in different ways.

Below, we create and plot a _Fit_ where the _MaskedDataset_ is trimmed from the left and right.
"""

# %%
settings_masked_dataset = htf.SettingsMaskedDataset(
    data_trim_left=20, data_trim_right=20
)

fit_gen = htf.agg.fit_generator_from_aggregator(
    aggregator=agg, settings_masked_dataset=settings_masked_dataset
)

htf.plot.FitDataset.residual_map(fit=list(fit_gen)[0])

# %%
"""
For your model-fitting project, you'll need to update the 'aggregator.py' module in the same way. This is why we have 
emphasised the object-oriented design of our model-fitting project through. This design makes it very easy to inspect 
results via the _Aggregator_ later on!
"""

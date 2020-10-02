import numpy as np

"""
In this tutorial, we run phases where the `Dataset` fitted by the phase is altered before the model-fitting
procedure is run. 

The `Dataset` is trimmed by an input number of pixels to the left and / or right.
"""


class Dataset:
    def __init__(self, data, noise_map):
        """A class containing the data and noise-map of a 1D line `Dataset`.

        Parameters
        ----------
        data : np.ndarray
            The array of the data, in arbitrary units.
        noise_map : np.ndarray
            An array describing the RMS standard deviation error in each data pixel, in arbitrary units.
        """
        self.data = data
        self.noise_map = noise_map

    @property
    def xvalues(self):
        return np.arange(self.data.shape[0])

    """
    The `MaskedDataset` that is fitted by an analysis is created using the method below.

    If the data_trim attributes are not None, they are used to trim the `Dataset` before creating the `MaskedDataset`.
    """

    def with_left_trimmed(self, data_trim_left):

        """Here, we use the existing `MaskedDataset` to create a trimmed `Dataset`."""

        data_trimmed = self.data[data_trim_left:]
        noise_map_trimmed = self.noise_map[data_trim_left:]

        return Dataset(data=data_trimmed, noise_map=noise_map_trimmed)

    def with_right_trimmed(self, data_trim_right):

        """We do the same as above, but removing data to the right."""

        data_trimmed = self.data[:-data_trim_right]
        noise_map_trimmed = self.noise_map[:-data_trim_right]

        return Dataset(data=data_trimmed, noise_map=noise_map_trimmed)


"""
We use a `SettingsMaskedDataset` class to choose the settings of how our `MaskedDataset` is setup for the model-fit,
specifically whether it is trimmed from the right and left.

This class includes tags, which customize the folders of the output of the phase. See the new module, `settings.py`
for a more complete description of tagging.
"""


class SettingsMaskedDataset:
    def __init__(self, data_trim_left=None, data_trim_right=None):
        """
        The settings of the `MaskedDataset` class, that in a phase are used to deterimne if the `MaskedDataset` is
        trimmed from the left and / or right before model-fitting.

        This class includes tags which are used to customize the output folders of a run dependent on the settings.

        Parameters
        ----------
        data_trim_left : int or None
            The number of pixels in 1D from the left (NumPy index 0) that the `Dataset` is trimmed.
        data_trim_right : int or None
            The number of pixels in 1D from the right (NumPy index -1) that the `Dataset` is trimmed.
        """

        self.data_trim_left = data_trim_left
        self.data_trim_right = data_trim_right

    @property
    def tag(self):
        """Generate a tag describin all settings customizing the `MaskedDataset`, which for this example only describes
        how the dataset it trimmed from the left and right.
        """
        return f"{self.data_trim_left_tag}{self.data_trim_right_tag}"

    @property
    def data_trim_left_tag(self):
        """Generate a data trim left tag, to customize phase names based on how much of the `Dataset` is trimmed to
        its left.

        This changes the phase name `settings` as follows:

        data_trim_left = None -> settings
        data_trim_left = 2 -> settings__trim_left_2
        data_trim_left = 10 -> settings__trim_left_10
        """
        if self.data_trim_left is None:
            return ""
        return f"__trim_left_{str(self.data_trim_left)}"

    @property
    def data_trim_right_tag(self):
        """Generate a data trim right tag, to customize phase names based on how much of the `Dataset` is trimmed to its right.

        This changes the phase name `settings` as follows:

        data_trim_right = None -> settings
        data_trim_right = 2 -> settings__trim_right_2
        data_trim_right = 10 -> settings__trim_right_10
        """
        if self.data_trim_right is None:
            return ""
        return f"__trim_right_{str(self.data_trim_right)}"


"""
The `MaskedDataset` class now has a new input, settings, which are the `SettingsMaskedDataset` which are used to 
customize the `MaskedDataset` that is created.
"""


class MaskedDataset:
    def __init__(self, dataset, mask, settings=SettingsMaskedDataset()):
        """
        A masked dataset, which is an image, noise-map and mask.

        Parameters
        ----------
        dataset: im.Dataset
            The `Dataset` (the image, noise-map, etc.)
        mask: msk.Mask2D
            The 1D mask that is applied to the `Dataset`.
        """

        """
        If the settings include a left trim, the function below trims the `Dataset` and mask before 
        settings up the `MaskedDataset`.
        """

        if settings.data_trim_left is not None:
            dataset = dataset.with_left_trimmed(data_trim_left=settings.data_trim_left)
            mask = mask[settings.data_trim_left :]

        """
        Now perform trimming from the right.
        """

        if settings.data_trim_right is not None:
            dataset = dataset.with_right_trimmed(
                data_trim_right=settings.data_trim_right
            )
            mask = mask[: -settings.data_trim_right]

        self.dataset = dataset
        self.mask = mask
        self.data = dataset.data * np.invert(mask)
        self.noise_map = dataset.noise_map * np.invert(mask)

        self.settings = settings

    @property
    def xvalues(self):
        return np.arange(self.data.shape[0])

    def signal_to_noise_map(self):
        return self.data / self.noise_map

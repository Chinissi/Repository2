import logging
import regex as re
import datetime
logger = logging.getLogger(__name__)
from great_expectations.execution_environment.data_connector.partitioner import(
    Partitioner
)

class RegexPartitioner(Partitioner):

    recognized_batch_parameters = {
        "regex",
        "sorters",
    }

    # defaults
    default_delim = '-'
    default_group_name = "group"


    def __init__(
        self,
        name,
        regex=None,
        sorters=None
    ):

        logger.debug("Constructing RegexPartitioner {!r}".format(name))
        super().__init__(name)

        self._regex = regex
        self._sorters = sorters
        self._partitions = {}

    @property
    def regex(self):
        return self._regex

    @regex.setter
    def regex(self, regex):
        self._regex = regex

    @property
    def sorters(self):
        return self._sorters

    def get_part(self, partition_name):
        # this will return : Part object (Will and Alex part - aka single part)
        pass

    def get_available_partition_names(self, paths):
        return [
            partition["partition_name"] for partition in self.get_available_partitions(paths)
        ]

    def get_available_partitions(self, paths):
        if len(self._partitions) > 0:
            return self._partitions

        partitions = [
            self._get_partitions(path)
            for path in paths
            if self._get_partitions(path) is not None
        ]
        # set self:
        self._partitions = partitions
        # return self._partitions (should this be another method?)
        return self._partitions

    def _get_partitions(self, path):
        temp_partitions = {}
        if self.regex is None:
            raise ValueError("REGEX is not defined")

        ####################################
        matches = re.match(self.regex, path)
        ####################################
        if matches is None:
            logger.warning("No match found for path: %s" % path)
            raise ValueError("No match found for path: %s" % path)

        else:
            # default case : there are no named ordered fields?
            # and add the name?
            if self.sorters is None:
                # then we want to use the defaults:
                # NOTE : matches begin with the full regex match at index=0 and then each matching group
                # and then each subsequent match in following indices.
                # this is why partition_definition_inner_dict is loaded with partition_params[i] as name
                # and matches[i+1] as value
                partition_definition_inner_dict = {}
                for i in range(len(matches)-1):
                    partition_param = self.default_group_name + "_" + str(i)
                    partition_definition_inner_dict[partition_param] = matches[i+1]
                temp_partitions["partition_definition"] = partition_definition_inner_dict
            partition_name_list = []
            for name in temp_partitions["partition_definition"].keys():
                partition_name_list.append(str(temp_partitions["partition_definition"][name]))
            partition_name = self.default_delim.join(partition_name_list)
            temp_partitions["partition_name"] = partition_name
        return temp_partitions

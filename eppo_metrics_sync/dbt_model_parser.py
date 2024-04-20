from collections import Counter
from itertools import chain


class DbtModelParser():

    def __init__(self, model):
        self.model = model
        self.eppo_entities = []
        self.eppo_timestamp = []
        self.eppo_facts = []
        self.eppo_properties = []
    
    def parse_columns(self):

        for column in self.model.get('columns'):

            tags = column.get('tags')

            if tags:
                column_entities = [t for t in tags if 'eppo_entity:' in t]

                if column_entities:
                    for column_entity in column_entities:
                        column_entity_split = column_entity.split(':')
                        if len(column_entity_split) != 2:
                            raise ValueError(
                                f'Invalid entity tag {column_entity} in model {self.model["name"]}'
                            )
                        else:
                            self.eppo_entities.append({
                                "entity_name": column_entity_split[1],
                                "column": column['name']
                            })
                        

                if 'eppo_timestamp' in tags:
                    self.eppo_timestamp = column["name"]

                if 'eppo_fact' in tags:
                    self.eppo_facts.append({
                        "name": column["name"],
                        "column": column["name"],
                        "description": column["description"]
                    })
                
                if 'eppo_property' in tags:
                    self.eppo_properties.append({
                        "name": column["name"],
                        "column": column["name"],
                        "description": column["description"]
                    })
    
    def validate(self):

        self.validation_errors = []

        # make sure there is at least one entity and exactly one timestamp
        if len(self.eppo_timestamp) == 0:
            self.validation_errors.append(
                'Exactly 1 column must be have tag "eppo_timestamp"'
            )
        
        if len(self.eppo_entities) == 0:
            self.validation_errors.append(
                'At least 1 column must have tag "eppo_entity:<entity_name>"'
            )
        
        # check that no columns are tagged to multiple Eppo fields (skip if there
        # is already a validation error)

        if len(self.validation_errors) == 0:
            # parse names from column list
            entity_names = [e['column'] for e in self.eppo_entities]
            timestamp_names = [self.eppo_timestamp]
            fact_names = [e['column'] for e in self.eppo_facts]
            property_names = [e['column'] for e in self.eppo_properties]

            all_names = Counter(chain.from_iterable(
                [entity_names, timestamp_names, fact_names, property_names]
            ))

            overlapping_columns = [item for item, count in all_names.items() if count > 1]

            if len(overlapping_columns):
                self.validation_errors.append(
                    f'The following columns had tags to multiple Eppo fields: {", ".join(overlapping_columns)}'
                )
            
        
        if len(self.validation_errors):
            raise ValueError(
                f'One or more errors parsing model: {self.model["name"]}: {", ".join(self.validation_errors)}'
            )

    
    def format(self):
        self.eppo_fact_source = {
            "name": self.model["name"],
            "sql": f"select * from {self.model['name']}",
            "timestamp_column": self.eppo_timestamp,
            "entities": self.eppo_entities,
            "facts": self.eppo_facts,
            "properties": self.eppo_properties
        }
    
    def build(self):
        self.parse_columns()
        self.validate()
        self.format()
        return self.eppo_fact_source

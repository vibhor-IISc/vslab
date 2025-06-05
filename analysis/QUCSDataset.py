import re
import numpy as np
from collections import defaultdict

class QUCSDataset:
    def __init__(self, filename):
        self.filename = filename
        self.data = defaultdict(lambda: {"indep": [], "values": [], "extra": None})
        self.independent_vars = {}
    
    def parse(self):
        with open(self.filename, 'r') as file:
            lines = file.readlines()

        current_key = None
        for line in lines:
            line = line.strip()

            # Skip closing tags like </indep> or </dep>
            if line.startswith("</"):
                current_key = None
                continue
            
            # Match independent variables
            match_indep = re.match(r"<indep\s+([\w\[\],]+)\s+(\d+)>", line)
            
            # Match dependent variables with multiple independent variables
            match_dep = re.match(r"<dep\s+([\w\[\],]+)\s+([\w\[\],]+(?:\s+[\w\[\],]+)*)>", line)

            if match_indep:
                current_key = match_indep.group(1)
                self.independent_vars[current_key] = []
            
            elif match_dep:
                current_key = match_dep.group(1)
                ref_indep = match_dep.group(2).split()
                
                self.data[current_key]["indep"] = ref_indep
                self.data[current_key]["values"] = []
                
            elif current_key in self.data or current_key in self.independent_vars:
                values = []
                for value in line.split():
                    try:
                        if 'j' in value:
                            value = value.replace(" ", "")
                        
                            # Fix complex numbers with scientific notation
                            value = re.sub(r'([\d\.]+e[\+\-]\d+)-j([\d\.]+e[\+\-]\d+)', r'\1-\2j', value)
                            value = re.sub(r'([\d\.]+e[\+\-]\d+)\+j([\d\.]+e[\+\-]\d+)', r'\1+\2j', value)
                        
                            parsed_value = complex(value)
                        else:
                            parsed_value = float(value)
                        
                        values.append(parsed_value)

                        # if 'j' in value:
                        #     value = value.replace(" ", "")
                        #     # value = re.sub(r'([\d\.]+)-j([\d\.]+)', r'\1-\2j', value)
                        #     # value = re.sub(r'([\d\.]+)\+j([\d\.]+)', r'\1+\2j', value)
                        #     value = re.sub(r'([\d\.]+e[\+\-]\d+)-j([\d\.]+e[\+\-]\d+)', r'\1-\2j', value)
                        #     value = re.sub(r'([\d\.]+e[\+\-]\d+)\+j([\d\.]+e[\+\-]\d+)', r'\1+\2j', value)

                        #     parsed_value = complex(value)
                        # else:
                        #     parsed_value = float(value)
                        # values.append(parsed_value)
                    except ValueError:
                        print(f"Warning: Could not parse value '{value}' in {current_key}")

                if current_key in self.independent_vars:
                    self.independent_vars[current_key].extend(values)
                else:
                    self.data[current_key]["values"].extend(values)
    
    def get_data(self):
        return self.data
    
    def get_independent_vars(self):
        return self.independent_vars



#  -------------------------

# Example usage:
# filename = r"C:\Users\user\.qucs\coupled_filter_prj\coupled_filter_sweep.dat"
# parser = QUCSDataset(filename)
# parser.parse()

# # # Print results
# # print("Independent Variables:", parser.get_independent_vars())
# # print("\nDependent Variables:", parser.get_data())

# GHz = 1e9
# nH = 1e-9

# freq = np.array(parser.get_independent_vars()['frequency'])/GHz
# Lq = np.array(parser.get_independent_vars()['Lq'])/nH
# s21 = np.array(parser.get_data()['S[2,1]']['values']).reshape(len(Lq),len(freq))

# import matplotlib.pyplot as plt
# plt.imshow(np.abs(s21), 
#            extent=(freq[0],freq[-1], Lq[-1],Lq[0]), 
#            aspect='auto')

# plt.xlabel('Freq (GHz)')
# plt.ylabel('LJ (nH)')
# plt.show()

# -*- coding: utf-8 -*-
"""
IB API - Object Oriented Programming (OOPs) Basics - Class

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""

class employee:
    def __init__(self,name,emp_id,exp,dept): #whenever the class employee is called, this function is run automatically
        self.Name = name 
        self.Emp_id = emp_id
        self.Exp = exp
        self.Dept = dept
        print(f"Employee {self.Emp_id} was created.")
    
    def calcSalary(self): #with passing self, we can reference the initiated variables
        if self.Exp > 5 and self.Dept == 'R&D':
            self.Salary = 200000
        else:
            self.Salary = 80000
        print(f"Salary for {self.Name} has been calculated to {self.Salary}")

    def empDesc(self):
        print(f'Employee {self.Name} from {self.Dept} has been working with us for {self.Exp} years.')

eemp1 = employee("Siggi", 1, 5, "R&D")
print(f"{eemp1.Name} is our employee.")
eemp1.calcSalary()
eemp1.empDesc()
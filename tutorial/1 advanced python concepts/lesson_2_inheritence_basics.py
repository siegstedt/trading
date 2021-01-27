# -*- coding: utf-8 -*-
"""
IB API - Object Oriented Programming (OOPs) Basics - Inheritance

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""

# inheritance let's us pass the properties of one class to another 
# this can help us preventing to reinvent the wheel and make more use of excising objects

class employee:
    def __init__(self,name="Siggi",emp_id=1,exp=5,dept="R&D"): # set some default parameters
        self.Name = name 
        self.Emp_id = emp_id
        self.Exp = exp
        self.Dept = dept
        print(f"Employee {self.Emp_id} was created.")
    
    def calcSalary(self):
        if self.Exp > 5 and self.Dept == 'R&D':
            self.Salary = 200000
        else:
            self.Salary = 80000
        print(f"Salary for {self.Name} has been calculated to {self.Salary}")

    def empDesc(self):
        print(f'Employee {self.Name} from {self.Dept} has been working with us for {self.Exp} years.')

class subEmployee(employee): # this sub class is inheriting from the employee class
    def __init__(self,name="Siggi",emp_id=1,exp=5,dept="R&D",sub_id="Mainz"): 
        # self.Name = name # redundant
        # self.Emp_id = emp_id # redundant
        # self.Exp = exp # redundant
        # self.Dept = dept # redundant
        super(subEmployee,self).__init__(name,emp_id,exp,dept) # this is similar to declaring the variables one by one
        self.Sub_id = sub_id
        print(f"Employee {self.Emp_id} for subsidiary {self.Sub_id} was created.")

    def calcSalary(self):
        self.Salary = min(max(1, self.Exp) * 30000,200000)
        print(f"Salary for {self.Name} has been calculated to {self.Salary}")

emp1_sub = subEmployee("Tina",2,4,"Mkt","Wiesbaden")
emp1_sub.calcSalary()
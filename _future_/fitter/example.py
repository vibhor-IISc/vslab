from fitter import Fitter
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 10, 100)

# Example 1: Lorentzian Fit

# ydata = Fitter.lorentzian(x, A=10, x0=5, w=1) + 0.05 * np.random.normal(size=len(x))

# fitter = Fitter("lorentzian")
# result = fitter.fit(x, ydata)  # Automatically estimates parameters
# print(result.fit_report())
# fitter.saveplot("test_lorentzian_fit.png")
# plt.clf()


# # # Example 2: S21 fit

# ydata = Fitter.S21(x, x0=5, amp=5, k = 1) + 0.05 * np.random.normal(size=len(x))
# fitter = Fitter("S21")
# result = fitter.fit(x, ydata)  # Automatically estimates parameters
# print(result.fit_report())
# fitter.saveplot("test_S21.png")
# plt.clf()

# # Example 3: S11 fit

# ydata = Fitter.S11(x, x0=5, amp=3, ke = 0.4, k = 1) + 0.05 * np.random.normal(size=len(x))
# fitter = Fitter("S11")
# result = fitter.fit(x, ydata)  # Automatically estimates parameters
# print(result.fit_report())
# fitter.saveplot("test_S11.png")
# plt.clf()

# Example 4: S21side fit

ydata = Fitter.S21side(x, x0=5, amp=4, ke = 0.4, k = 1) + 0.05 * np.random.normal(size=len(x))
fitter = Fitter("S21side")
result = fitter.fit(x, ydata)  # Automatically estimates parameters
print(result.fit_report())
fitter.saveplot("test_S21side.png")
plt.clf()


# # Example 5: linear fit

# ydata = Fitter.linear(x, m=1, b = 10) + 0.05 * np.random.normal(size=len(x))
# fitter = Fitter("linear")
# result = fitter.fit(x, ydata)  # Automatically estimates parameters
# print(result.fit_report())
# fitter.saveplot("test_linear_fit.png")
# plt.clf()

# # Example 6: quadratic fit

# ydata = Fitter.quadratic(x, a=1, b = 10, c=3) + 0.05 * np.random.normal(size=len(x))
# fitter = Fitter("quadratic")
# result = fitter.fit(x, ydata)  # Automatically estimates parameters
# print(result.fit_report())
# fitter.saveplot("test_quadratic_fit.png")
# plt.clf()


# # Example 7: Exponential Fit

# ydata = Fitter.exponential(x, A=5, tau=2, C=1) + 0.05 * np.random.normal(size=len(x))
# fitter = Fitter("exponential")
# result = fitter.fit(x, ydata)  # Automatically estimates parameters
# print(result.fit_report())
# fitter.saveplot("test_exponential_fit.png")
plt.clf()


# Get best fit parameters and their stderr
best_params = fitter.best_fit_params()
print("\nBest fit parameters and their stderr:")
for param_name, param_info in best_params.items():
    print(f"{param_name}: value = {param_info['value']}, stderr = {param_info['stderr']}")

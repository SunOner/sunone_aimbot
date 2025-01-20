import numpy as np
from scipy.optimize import minimize
from scipy.integrate import ode

def target_dynamics(t, state, a):
    """
    Defines the dynamics of the target: acceleration only in x-direction.
    state = [x, y, vx, vy]
    """
    x, y, vx, vy = state
    return [vx, vy, a, 0]  # acceleration only in x-direction

def interceptor_dynamics(t, state, v, theta):
    """
    Defines the dynamics of the interceptor: constant speed, direction by theta.
    state = [x, y]
    """
    x, y = state
    return [v * np.cos(theta), v * np.sin(theta)]

def cost_function(params, v, target_init, a, end_time):
    """
    Cost function to minimize. Here we minimize the distance at t = end_time.
    params = [angle in radians]
    """
    theta = params[0]
    
    # Solve target's trajectory
    target = ode(target_dynamics).set_integrator('vode', method='adams')
    target.set_initial_value(target_init, 0).set_f_params(a)
    target_states = [target_init]
    
    dt = 0.01  # time step for integration
    while target.successful() and target.t < end_time:
        target.integrate(target.t + dt)
        target_states.append([target.y[0], target.y[1]])
    
    # Solve interceptor's trajectory
    interceptor = ode(interceptor_dynamics).set_integrator('vode', method='adams')
    interceptor.set_initial_value([0, 0], 0).set_f_params(v, theta)
    interceptor_states = [[0, 0]]
    
    while interceptor.successful() and interceptor.t < end_time:
        interceptor.integrate(interceptor.t + dt)
        interceptor_states.append([interceptor.y[0], interceptor.y[1]])
    
    # Calculate the distance at the end time
    target_pos = target_states[-1][:2]  # x, y of target at end time
    interceptor_pos = interceptor_states[-1]  # x, y of interceptor at end time
    distance = np.linalg.norm(np.array(target_pos) - np.array(interceptor_pos))
    
    return distance

def find_optimal_intercept(v, target_init, a, end_time):
    """
    Find the optimal angle for interception.
    """
    initial_guess = [np.pi/4]  # Start with 45 degrees as initial guess
    result = minimize(cost_function, initial_guess, args=(v, target_init, a, end_time), 
                      method='L-BFGS-B', bounds=[(0, np.pi)])
    return result.x[0], result.fun

# Example usage:
v = 10  # interceptor speed
target_init = [0, 0, 5, 0]  # Initial state for target: [x, y, vx, vy]
a = 2  # Acceleration of target in x-direction
end_time = 10  # Let's say we aim to intercept before this time

optimal_angle, min_distance = find_optimal_intercept(v, target_init, a, end_time)
print(f"Optimal angle: {np.degrees(optimal_angle):.2f} degrees")
print(f"Minimum distance at end time: {min_distance:.2f}")
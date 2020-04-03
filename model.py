import math
import pandas as pd
import numpy as np
import scipy.integrate
from datetime import timedelta
import shared
# import world_data
# import population

def model(Y, x, N, beta0, days0, beta1, gamma, sigma):
    # :param array x: Time step (days)
    # :param int N: Population
    # :param float beta: The parameter controlling how often a susceptible-infected contact results in a new infection.
    # :param float gamma: The rate an infected recovers and moves into the resistant phase.
    # :param float sigma: The rate at which an exposed person becomes infective.

    S, E, I, R = Y

    beta = beta0 if x < days0 else beta1

    dS = - beta * S * I / N
    dE = beta * S * I / N - sigma * E
    dI = sigma * E - gamma * I
    dR = gamma * I
    return dS, dE, dI, dR


def solve(model, population, E0, beta0, days0, beta1, gamma, sigma, days_total):
    X = np.arange(days_total)  # time steps list
    N0 = population - E0, E0, 0, 0  # S, E, I, R at initial step

    y_data_var = scipy.integrate.odeint(model, N0, X, args=(population, beta0, days0, beta1, gamma, sigma))

    S, E, I, R = y_data_var.T  # transpose and unpack
    return X, S, E, I, R  # note these are all arrays


def run_SEIR(population, intensive_units, date_of_first_infection, date_of_lockdown, mean_days_icu):

    # --- external parameters ---
    days_total = 365  # total days to model
    # dataOffset = 'auto'  # position of real world data relative to model in whole days.
    # 'auto' will choose optimal offset based on matching of deaths curves

    E0 = 1  # number of exposed people at initial time step
    r0 = 3.0  # https://en.wikipedia.org/wiki/Basic_reproduction_number
    r1 = 1.1  # reproduction number after quarantine measures - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3539694

    # --- derived parameters ---
    days_before_lockdown = (date_of_lockdown - date_of_first_infection).days

    # almost half infections take place before symptom onset (Drosten)
    # https://www.medrxiv.org/content/10.1101/2020.03.08.20032946v1.full.pdf
    days_presymptomatic = 2.5
    days_to_incubation = 5.2

    # sigma: The rate at which an exposed person becomes infective.  symptom onset - presympomatic
    sigma = 1.0 / (days_to_incubation - days_presymptomatic)

    # for SEIR: generation_time = 1/sigma + 0.5 * 1/gamma = timeFromInfectionToInfectiousness + timeInfectious  https://en.wikipedia.org/wiki/Serial_interval
    generation_time = 4.6  # https://www.medrxiv.org/content/10.1101/2020.03.05.20031815v1  http://www.cidrap.umn.edu/news-perspective/2020/03/short-time-between-serial-covid-19-cases-may-hinder-containment

    # gamma: The rate an infectious person recovers and moves into the resistant phase.
    # Note that for the model it only means he does not infect anybody any more.
    gamma = 1.0 / (2.0 * (generation_time - 1.0 / sigma))

    percent_asymptomatic = 0.35  # https://www.zmescience.com/medicine/iceland-testing-covid-19-0523/  but virus can already be found in throat 2.5 days before symptoms (Drosten)
    # wild guess! italy:16? germany:4 south korea: 4?  a lot of the mild cases will go undetected  assuming 100% correct tests
    percent_cases_detected = (1.0 - percent_asymptomatic) / 20.0

    days_in_hospital = 12
    days_infectious = 1.0 / gamma  # better timeInfectious?

    # lag, whole days - need sources
    presymptomatic_lag = round(days_presymptomatic)  # effort probably not worth to be more precise than 1 day
    communication_lag = 2
    test_lag = 3
    symptom_to_hospital_lag = 5
    hospital_to_icu_lag = 5

    infectionFatalityRateA = 0.01  # Diamond Princess, age corrected
    infectionFatalityRateB = infectionFatalityRateA * 3.0  # higher lethality without ICU - by how much?  even higher without oxygen and meds
    icuRate = infectionFatalityRateA * 2  # Imperial College NPI study: hospitalized/ICU/fatal = 6/2/1

    beta0 = r0 * gamma  # The parameter controlling how often a susceptible-infected contact results in a new infection.
    beta1 = r1 * gamma  # beta0 is used during days0 phase, beta1 after days0

    s1 = 0.5 * (-(sigma + gamma) + math.sqrt((sigma + gamma) ** 2 + 4 * sigma * gamma * (
                r0 - 1)))  # https://hal.archives-ouvertes.fr/hal-00657584/document page 13
    # doublingTime = (math.log(2.0, math.e) / s1)

    X, S, E, I, R = solve(model, population, E0, beta0, days_before_lockdown, beta1, gamma, sigma, days_total)

    demand_dict = {'days': X,
                   'susceptible': S,
                   'exposed': E,
                   'infectious': I,
                   'recovered': R,
                   }

    df = pd.DataFrame(demand_dict)
    df['date'] = df['days'].apply(lambda x: date_of_first_infection + timedelta(days=x))
    df = df.applymap(lambda x: round(x) if isinstance(x, float) else x)


    # Feature engineering
    df['needs_icu'] = df.apply(lambda x: round(x['infectious'] * icuRate), axis=1)
    df['needs_icu'] = df['needs_icu'].shift(10).rolling(window=mean_days_icu).sum()
    df.drop(columns=['exposed'], inplace=True)


    # # derived arrays
    # F = I * percent_cases_detected
    # needs_icu = I * icuRate * days_in_hospital / days_infectious  # scale for short infectious time vs. real time in hospital
    # # P = I / population * 1_000_000  # probability of random person to be infected
    #
    # # timeline: exposed, infectious, symptoms, at home, hospital, ICU
    # F = shared.delay(F,
    #                  days_presymptomatic + symptom_to_hospital_lag + test_lag + communication_lag)  # found in tests and officially announced; from I
    # U = shared.delay(needs_icu, days_presymptomatic + symptom_to_hospital_lag + hospital_to_icu_lag)  # ICU  from I before delay
    # U = shared.delay(U, round(
    #     (days_in_hospital / days_infectious - 1) * days_infectious))  # ??? delay by scaling? todo: think this through
    #
    # # cumulate found --> cases
    # # FC = np.cumsum(F)
    #
    # # estimate deaths from recovered
    # D = np.zeros(days_total)
    # RPrev = 0
    # DPrev = 0
    # for i, x in enumerate(X):
    #     IFR = infectionFatalityRateA if U[i] <= intensive_units else infectionFatalityRateB
    #     D[i] = DPrev + IFR * (R[i] - RPrev)
    #     RPrev = R[i]
    #     DPrev = D[i]
    #
    # D = shared.delay(D,
    #                  - days_infectious + days_presymptomatic
    #                  + symptom_to_hospital_lag + days_in_hospital
    #                  + communication_lag)  # deaths  from R





    line_plot_data = df.melt(id_vars=['date'],
                             value_vars=['susceptible', 'infectious', 'recovered', 'needs_icu'],
                             value_name='count',
                             var_name='type')

    return line_plot_data

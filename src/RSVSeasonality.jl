"""
    RSVSeasonality

Research package for climate-dependent RSV transmission models.

Provides aggregate surveillance observation likelihoods.

See `notes/modelling-methodology.md` for the proposed model interfaces and design.
"""
module RSVSeasonality

export JapanObservation, SentinelSites, SentinelReporting,
       ReportingUnknown, ReportingIncomplete, ReportingComplete,
       USObservation, ReportedTests, LabMethod, PCR, Antigen,
       LabCoverage, AbsentWeek, ZeroTestWeek, TestedWeek, lab_coverage, observed_positivity,
       NB2, BinomialPositivity, BetaBinomialPositivity, observation_loglikelihood

include("observations.jl")

end

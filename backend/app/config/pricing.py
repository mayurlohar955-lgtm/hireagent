


# Change these numbers anytime — they control everything
PLANS = {
    "trial": {
        "name":           "Free Trial",
        "price_inr":      0,
        "price_usd":      0,
        # change trial length here
        "trial_days":     14,         
        "max_jobs":       3,
        "max_resumes":    50,
        "features":       ["JD Writer", "Resume Screening", "Pipeline Board"],
    },
    "starter": {
        "name":           "Starter",
        # change monthly price here
        "price_inr":      9999,       
        "price_usd":      120,
        "trial_days":     0,
        "max_jobs":       10,
        "max_resumes":    200,
        "features":       ["JD Writer", "Resume Screening", "Pipeline Board", "Email Support"],
    },
    "growth": {
        "name":           "Growth",
        # change monthly price here
        "price_inr":      29999,      
        "price_usd":      360,
        "trial_days":     0,
        "max_jobs":       50,
        "max_resumes":    1000,
        "features":       ["Everything in Starter", "Bulk Upload", "Analytics", "Priority Support"],
    },
    "scale": {
        "name":           "Scale",
        # change monthly price here
        "price_inr":      79999,      
        "price_usd":      960,
        "trial_days":     0,
        "max_jobs":       999,
        "max_resumes":    9999,
        "features":       ["Everything in Growth", "White-label", "Dedicated Support", "Custom Integrations"],
    },
}





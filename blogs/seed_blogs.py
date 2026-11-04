import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from blogs.models import BlogPost

ARTICLES = [
    {
        "title": "Electricity Submeter Billing Formula for Indian Landlords & Hostels",
        "slug": "electricity-submeter-billing-formula-india",
        "category": "Electricity Submetering",
        "excerpt": "A step-by-step practical guide on calculating electricity submeter bills accurately, handling meter rollovers, applying state tariff rates, and preventing tenant disputes.",
        "cover_image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&auto=format&fit=crop&q=80",
        "author_name": "Gourav Berwal",
        "author_role": "Founder, KirayaSaathi",
        "read_time": "6 min read",
        "tags": "Electricity Submeter, Electricity Billing, Rent Calculation, Hostel Management, Sub-metering India",
        "is_featured": True,
        "is_published": True,
        "views_count": 1420,
        "content": """
<h2>Why Electricity Sub-Metering Causes the Most Landlord-Tenant Friction</h2>
<p>In Indian rental properties—especially student hostels, paying guest (PG) accommodations, and multi-floor independent houses—electricity submeter calculations are the #1 source of arguments at the beginning of every month. Common complaints include:</p>
<ul>
  <li><em>"I wasn't in the room for 10 days, why is my bill so high?"</em></li>
  <li><em>"Did the landlord apply the domestic tariff or commercial rate?"</em></li>
  <li><em>"The meter jumped numbers, how was this calculated?"</em></li>
</ul>
<p>By implementing a transparent formula and digital record-keeping system with KirayaSaathi, property owners can completely automate this process and eliminate doubt.</p>

<h2>The Standard Electricity Submeter Formula</h2>
<p>The standard consumption formula used across Indian residential properties is straightforward:</p>
<blockquote>
  <strong>Units Consumed (kWh) = Current Meter Reading - Previous Meter Reading</strong><br>
  <strong>Total Electricity Charge (₹) = Units Consumed × Approved Rate per Unit (₹/kWh)</strong>
</blockquote>

<h3>Example Calculation:</h3>
<ul>
  <li>Previous Meter Reading (1st Oct): <strong>4,250 units</strong></li>
  <li>Current Meter Reading (1st Nov): <strong>4,410 units</strong></li>
  <li>Units Consumed: 4,410 - 4,250 = <strong>160 units</strong></li>
  <li>Rate per Unit (as per rent agreement): <strong>₹9.00</strong></li>
  <li>Total Electricity Bill: 160 × ₹9.00 = <strong>₹1,440.00</strong></li>
</ul>

<h2>Handling Sub-Meter Rollover (Mechanical & Digital)</h2>
<p>When an analog or 4-digit digital submeter reaches <strong>9,999</strong>, the next reading rolls over to <strong>0001</strong>. If a landlord naively subtracts 9,999 from 0001, basic calculator software outputs a negative number or throws an error.</p>
<p><strong>The Correct Rollover Formula:</strong></p>
<blockquote>
  <strong>Units Consumed = (Max Capacity - Previous Reading) + Current Reading</strong><br>
  For a 9,999 capacity meter: (10,000 - 9,920) + 45 = 80 + 45 = <strong>125 units</strong>.
</blockquote>
<p>KirayaSaathi automatically detects meter rollovers and calculates the exact usage without requiring manual intervention.</p>

<h2>3 Golden Rules for Dispute-Free Utility Billing</h2>
<ol>
  <li><strong>Take a Photo of the Meter on the 1st of Every Month:</strong> Always keep a digital photo of each room's submeter timestamped with your phone camera.</li>
  <li><strong>Explicitly State the Per-Unit Rate in the Rent Agreement:</strong> Do not rely on verbal agreements. State whether common area electricity (staircase lights, water pump) is included or divided equally.</li>
  <li><strong>Provide an Itemized Invoice:</strong> Never just text <em>"Rent ₹8,000 + Light bill ₹1,200"</em>. Send a structured digital receipt showing previous reading, current reading, total units, and unit rate.</li>
</ol>
        """,
    },
    {
        "title": "How to Draft a Legally Enforceable Rent Agreement in India (11-Month Rule vs Registered Lease)",
        "slug": "legally-enforceable-rent-agreement-guide-india",
        "category": "Rent Laws & Agreements",
        "excerpt": "Understand why 11-month rental agreements are standard in India, when registration under the Registration Act 1908 is mandatory, state stamp duty costs, and essential landlord-protection clauses.",
        "cover_image": "https://images.unsplash.com/photo-1450133064473-71024230f91b?w=1200&auto=format&fit=crop&q=80",
        "author_name": "KirayaSaathi Legal Team",
        "author_role": "Legal & Compliance Specialists",
        "read_time": "8 min read",
        "tags": "Rent Agreement, Indian Rental Laws, 11 Month Agreement, Police Verification, Stamp Duty",
        "is_featured": False,
        "is_published": True,
        "views_count": 2180,
        "content": """
<h2>Why Are Most Rental Agreements in India Signed for 11 Months?</h2>
<p>Under <strong>Section 17 of the Registration Act, 1908</strong>, any lease or tenancy agreement for immovable property that exceeds 11 months (i.e. 12 months or longer) is <em>legally required to be officially registered</em> with the local Sub-Registrar of Assurances.</p>
<p>Registration requires both parties to physically visit the Sub-Registrar office, pay state-specific registration fees, and pay higher stamp duty. By structuring the initial tenure as <strong>11 months with a renewal option</strong>, property owners and tenants legally avoid the mandatory registration requirement while maintaining a binding contract.</p>

<h2>Key Clauses Every Indian Property Owner Must Include</h2>
<ul>
  <li><strong>Lock-in Period & Notice Period:</strong> Specify a mandatory notice period (typically 30 days) before either party can terminate the tenancy.</li>
  <li><strong>Security Deposit Refund Timeline:</strong> State explicitly that the security deposit will be refunded within 7 to 15 days after room handover, subject to deductions for unpaid utility bills or physical damages beyond normal wear and tear.</li>
  <li><strong>Maintenance & Repair Allocation:</strong> Define who pays for minor repairs (e.g. tap washer replacement, light bulbs) versus major structural repairs (e.g. wall seepage, roof repair).</li>
  <li><strong>Subletting Prohibition:</strong> Explicitly forbid the tenant from subleasing any portion of the premises to third parties without prior written consent.</li>
  <li><strong>Electricity Sub-metering Rate:</strong> Mention the agreed per-unit rate and monthly billing cycle date.</li>
</ul>

<h2>Mandatory Police Verification: Why You Cannot Skip It</h2>
<p>In almost all major Indian cities—including Delhi NCR, Mumbai, Bengaluru, Pune, Indore, and Hyderabad—local police commissionerate notifications mandate tenant police verification under Section 188 of the Indian Penal Code (IPC).</p>
<p>Failure to complete tenant verification can result in fines and legal complications if a tenant is involved in criminal activity. KirayaSaathi allows property owners to store tenant Aadhaar cards, permanent address proofs, and police verification forms digitally in one secure place.</p>
        """,
    },
    {
        "title": "Top 7 Tenant Screening Checklist Tips Every PG & Flat Owner Must Know",
        "slug": "tenant-screening-checklist-pg-flat-owners",
        "category": "Tenant Management",
        "excerpt": "A practical checklist to verify prospective tenants, check employment or college credentials, secure deposit safety, and maintain a safe residential environment.",
        "cover_image": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1200&auto=format&fit=crop&q=80",
        "author_name": "Gourav Berwal",
        "author_role": "Founder, KirayaSaathi",
        "read_time": "5 min read",
        "tags": "Tenant Screening, PG Verification, Tenant Background Check, Rental Safety",
        "is_featured": False,
        "is_published": True,
        "views_count": 980,
        "content": """
<h2>Screening Before Handing Over the Keys Saves Months of Headaches</h2>
<p>Every experienced property owner in India knows: <em>It is ten times easier to reject an unsuitable tenant before move-in than to evict a defaulting tenant after move-in.</em></p>
<p>Here is the proven 7-step tenant screening protocol implemented by the top PG and hostel operators on KirayaSaathi.</p>

<h2>The 7-Point Screening Checklist</h2>
<ol>
  <li><strong>Government Photo ID Proof:</strong> Collect a clean digital copy of the tenant's Aadhaar Card, Passport, or Voter ID. Always cross-verify the address.</li>
  <li><strong>Proof of Occupation / Student Enrollment:</strong>
    <ul>
      <li>For working professionals: Official company ID card or recent salary slip/offer letter.</li>
      <li>For students: College ID card and confirmation of current semester enrollment.</li>
    </ul>
  </li>
  <li><strong>Permanent Family / Emergency Contact:</strong> Always take the mobile number and address of a parent or guardian. Test call the number before confirming the booking.</li>
  <li><strong>Previous Landlord Reference Check:</strong> Ask for the contact number of the landlord at their previous residence. A 2-minute phone call asking <em>"Did they pay rent on time and leave the room in good condition?"</em> provides priceless peace of mind.</li>
  <li><strong>Strict Policy on Full Security Deposit:</strong> Never allow move-in on a partial security deposit or promises of <em>"I will pay the rest next week"</em>. Collect the agreed deposit via digital payment (UPI / Bank transfer) for complete transaction traceability.</li>
  <li><strong>Digital Move-in Inventory Check:</strong> Walk through the room with the tenant on day one. Note down the working status of fan, geyser, taps, switches, and current electricity submeter reading.</li>
  <li><strong>Signed Rules & Regulations Acceptance:</strong> Ensure the tenant signs the house rules covering guest entry, quiet hours, smoking/alcohol policies, and gate closing timings.</li>
</ol>
        """,
    },
    {
        "title": "Managing Hostel & PG Vacancies: Proven Strategies to Maintain 95%+ Occupancy in 2026",
        "slug": "hostel-pg-vacancy-management-strategies-2026",
        "category": "PG & Hostel Guide",
        "excerpt": "Discover how leading student hostels and working professional PGs keep their rooms 95%+ occupied year-round using digital rent receipts for HRA, high-speed amenities, and referral programs.",
        "cover_image": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=1200&auto=format&fit=crop&q=80",
        "author_name": "KirayaSaathi Editorial Team",
        "author_role": "Hostel Operations Specialist",
        "read_time": "7 min read",
        "tags": "Hostel Vacancy, PG Occupancy, Rental Business India, Student Housing, HRA Receipts",
        "is_featured": False,
        "is_published": True,
        "views_count": 1740,
        "content": """
<h2>The Cost of an Empty Bed in a Student Hostel or PG</h2>
<p>In student hubs like Kota, Indore, Pune, Bengaluru, and Delhi Mukherjee Nagar, every vacant bed represents a permanent loss of ₹5,000 to ₹12,000 per month that can never be recovered.</p>
<p>Top operators achieve year-round 95%+ occupancy not by lowering prices, but by addressing what modern tenants value most.</p>

<h2>Strategy 1: Provide Instant Digital Rent Receipts with Landlord PAN for HRA</h2>
<p>Working professionals actively seek out accommodations that provide GST/PAN compliant rent receipts for claiming <strong>House Rent Allowance (HRA) tax deductions</strong> under Section 10(13A). Landlords who only offer handwritten scraps lose high-quality IT and corporate tenants.</p>
<p>With KirayaSaathi, you can generate and download branded PDF receipts with one click and WhatsApp them directly to tenants.</p>

<h2>Strategy 2: High-Speed Mesh Wi-Fi & Power Backup</h2>
<p>In 2026, Wi-Fi is no longer an optional perk—it is an absolute necessity. Students taking online coaching and professionals working remotely will immediately leave a PG with unstable internet. Invest in commercial fiber connections with battery inverter backup.</p>

<h2>Strategy 3: Implement an Early Notice Incentive</h2>
<p>Require 30 days notice before checkout, and offer a ₹500 discount on the final month's bill if the tenant gives 45 days advance notice. This gives you ample time to advertise and pre-book the bed before the current occupant moves out.</p>

<h2>Strategy 4: Student & Tenant Referral Bonuses</h2>
<p>Turn your current satisfied residents into your best marketing team. Offer ₹1,000 rent credit for every friend or college batchmate they refer who signs a minimum 6-month stay.</p>
        """,
    },
]

for art in ARTICLES:
    post, created = BlogPost.objects.update_or_create(
        slug=art["slug"],
        defaults=art,
    )
    status_str = "Created" if created else "Updated"
    print(f"[{status_str}] {post.title} (Slug: {post.slug})")

print(f"Total blog articles in database: {BlogPost.objects.count()}")

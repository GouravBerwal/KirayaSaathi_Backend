import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from blogs.models import BlogPost

ARTICLES = [
    {
    "title": "Electricity Submeter Billing & Auto-Rollover Formula for Indian Landlords & Hostels",
    "slug": "electricity-submeter-billing-formula-india",
    "category": "Electricity Submetering",
    "excerpt": "A mathematical, regulatory, and operational whitepaper for Indian landlords, student hostels, and PG operators. Master consumption formulas, submeter rollovers, fixed demand load sharing, and legal compliance under the Indian Electricity Act 2003.",
    "cover_image": "/images/blogs/submeter_formula_guide.webp",
    "author_name": "Gourav Berwal",
    "author_role": "Founder & Creator of KirayaSaathi",
    "read_time": "8 min read",
    "tags": "Electricity Submeter, Smart Rental and Tenant Management System, Submeter Billing Formula India, Hostel Management, PG Management, Landlord Electricity Rules, Electricity Act 2003, Rent Calculation",
    "is_featured": True,
    "is_published": True,
    "views_count": 0,
    "content": """
<h2>1. Executive Summary: The ₹12,000/Month Hidden Friction in Indian Rentals</h2>
<p>In the Indian rental ecosystem—encompassing student hostels in coaching hubs like Kota and Indore, paying guest (PG) accommodations in Bengaluru and Pune, and multi-unit residential properties in Delhi NCR and Mumbai—<strong>electricity submeter calculation is the primary catalyst for landlord-tenant friction</strong>.</p>
<p>Unlike standard utility billing where a single municipal meter serves a detached home, multi-tenant properties operate on a hub-and-spoke electrical distribution model: one main DISCOM bulk connection feeding dozens of internal submeters. When utility calculations rely on manual paper registers, pencil arithmetic, or loose WhatsApp texts, three recurring failure modes emerge:</p>
<ul>
  <li><strong>Unaccounted Sub-Meter Rollover:</strong> Analog or 4-digit digital submeters cycling from 9,999 to 0001, resulting in negative consumption figures or absurd charges.</li>
  <li><strong>Common Area Load Discrepancies:</strong> Friction regarding who pays for the 1.5 HP water motor pump, hallway lighting, CCTV power supplies, and inverter battery standby draw.</li>
  <li><strong>Tariff Slab Misunderstandings:</strong> Tenants accusing landlords of illegal electricity resale when their per-unit charge exceeds the baseline domestic 0-100 unit government subsidized slab.</li>
</ul>
<p>This engineering whitepaper provides the exact mathematical formulas, regulatory boundaries under the <em>Indian Electricity Act 2003</em>, and digital automation protocols to eliminate 100% of submeter disputes.</p>

<hr/>

<h2>2. The Core Mathematical Formulas</h2>
<h3>2.1 Standard Linear Consumption Formula</h3>
<p>For standard operational cycles where the meter has not reached maximum capacity:</p>
<blockquote>
  <strong>Units Consumed (kWh) = Current Meter Reading (R<sub>current</sub>) - Previous Meter Reading (R<sub>previous</sub>)</strong><br/><br/>
  <strong>Total Room Electricity Cost (₹) = Units Consumed (kWh) × Agreed Contractual Unit Rate (₹/kWh)</strong>
</blockquote>

<h4>Mathematical Verification:</h4>
<ul>
  <li>Previous Meter Reading (01 Oct, 10:00 AM): <strong>4,250.0 kWh</strong></li>
  <li>Current Meter Reading (01 Nov, 10:00 AM): <strong>4,410.0 kWh</strong></li>
  <li>Net Units Consumed: 4,410.0 - 4,250.0 = <strong>160.0 kWh</strong></li>
  <li>Contractual Rate: <strong>₹9.50 per unit</strong></li>
  <li><strong>Net Charge: 160 × ₹9.50 = ₹1,520.00</strong></li>
</ul>

<h3>2.2 The Sub-Meter Rollover Theorem (Capacity Overflow Handling)</h3>
<p>Analog disc meters and standard 4-digit digital LCD submeters have a maximum counter capacity of <strong>9,999.9 kWh</strong>. On the 10,000th unit, the physical register rolls over to <strong>0000.0</strong>.</p>
<p>If a naive operator evaluates <code>Current - Previous</code>, the calculation yields:<br/>
<code>0045 - 9920 = -9,875 units</code>, producing calculation errors or accidental billing waivers.</p>

<blockquote>
  <strong>The Universal Rollover Formula:</strong><br/>
  <strong>Units Consumed (kWh) = (Meter Maximum Modulo - R<sub>previous</sub>) + R<sub>current</sub></strong><br/><br/>
  <em>Where Meter Maximum Modulo is 10,000 for a 4-digit meter (or 100,000 for a 5-digit meter).</em>
</blockquote>

<h4>Worked Rollover Example:</h4>
<ul>
  <li>Meter Type: 4-Digit Digital LCD (Capacity 9,999)</li>
  <li>Previous Reading (1st April): <strong>9,920 kWh</strong></li>
  <li>Current Reading (1st May): <strong>0,045 kWh</strong></li>
  <li>Formula Application: <code>(10,000 - 9,920) + 45 = 80 + 45 = 125 units</code></li>
  <li>At ₹9.00/unit: <code>125 × ₹9.00 = ₹1,125.00</code></li>
</ul>
<p><strong>KirayaSaathi Engineering Note:</strong> Our cloud billing engine automatically detects if <code>R<sub>current</sub> &lt; R<sub>previous</sub></code> and applies the modulo rollover algorithm instantly, alerting the property manager while preventing invoice corruption.</p>

<hr/>

<h2>3. Common Area Load (CAM) Allocation Framework</h2>
<p>One of the most contentious points in student hostels and independent rental floors is common electricity consumption. Shared infrastructure typically includes:</p>
<ol>
  <li><strong>Borewell / Submersible Water Pump:</strong> 1.5 HP to 2.0 HP motor running 1.5 hours daily (~2.2 kWh/day = ~66 kWh/month).</li>
  <li><strong>Common Corridor & Staircase Illumination:</strong> 4 LED battens (20W each) running 10 hours daily (~0.8 kWh/day = ~24 kWh/month).</li>
  <li><strong>Central Wi-Fi Mesh & CCTV Surveillance:</strong> Continuous 40W draw (~29 kWh/month).</li>
</ol>

<blockquote>
  <strong>Fair Common Utility Apportionment Formula:</strong><br/>
  <strong>Per-Tenant Common Charge = Total Common Meter Units × Unit Rate / Active Occupied Beds</strong>
</blockquote>
<p><em>Crucial Best Practice:</em> Never divide common units by total capacity if rooms are vacant; the owner absorbs vacant room shares to maintain contractual fairness with existing tenants.</p>

<hr/>

<h2>4. Regulatory & Legal Compliance (Indian Electricity Act, 2003)</h2>
<p>A common inquiry from landlords and PG operators is: <strong>"Is it legal to charge ₹8 to ₹11 per unit on sub-meters in India?"</strong></p>
<p>Under <strong>Section 126 and Section 135 of the Indian Electricity Act 2003</strong>, commercial resale of electricity without a distribution license is prohibited. However, state electricity regulatory commissions (SERCs) like DERC (Delhi), MSEDCL (Maharashtra), and UPPCL (Uttar Pradesh) recognize that property owners installing private submeters for internal cost recovery are <em>not acting as public utilities</em>, provided that:</p>
<ul>
  <li><strong>Blended Cost Recovery:</strong> The total sum collected across all submeters plus common areas does not generate arbitrary commercial profit beyond the actual DISCOM billing plus fixed operational costs (transformer maintenance, load sanctioning, line transmission loss).</li>
  <li><strong>Contractual Transparency:</strong> The exact per-unit rate must be explicitly stated in the executed 11-month rent agreement, signed by both tenant and landlord prior to possession.</li>
  <li><strong>Itemized Proof:</strong> The landlord must maintain digital photo logs of submeter readings and furnish itemized receipts on demand.</li>
</ul>

<hr/>

<h2>5. The 5-Point Dispute-Zero Operating Protocol</h2>
<p>Leading property operators managing 50 to 500+ beds adhere to this 5-point operational checklist every month:</p>
<ol>
  <li><strong>Timestamped Photographic Record:</strong> Take a clear photo of the room submeter dial on the 1st of every month between 9:00 AM and 1:00 PM. Store it in cloud storage via KirayaSaathi.</li>
  <li><strong>Dual Signature Move-In Sheet:</strong> Record the initial base reading on the handover inspection sheet before handing over room keys.</li>
  <li><strong>Automated PDF Invoicing:</strong> Eliminate handwritten slips. Issue a structured PDF receipt that displays: <code>Previous Reading | Current Reading | Total Units | Rate per Unit | Calculated Total</code>.</li>
  <li><strong>Clear Discom Tariff Disclosure:</strong> Explain whether the per-unit rate includes fixed meter demand charges and water pump allocation.</li>
  <li><strong>Digital Payment Reconciliation:</strong> Accept utility payments via UPI, bank transfer, or QR code so that transaction timestamps match monthly invoice numbers.</li>
</ol>

<hr/>

<h2>6. Automate Your Rental Property Billing with KirayaSaathi</h2>
<p>Manual submeter calculations, spreadsheet formulas, and paper registers belong in the past. <strong>KirayaSaathi</strong> gives Indian property owners, PG operators, and student hostel managers an intelligent, cloud-hosted platform:</p>
<ul>
  <li>Automatic submeter rollover detection and calculation.</li>
  <li>1-click PDF rent receipt generation with landlord PAN for tenant HRA claims.</li>
  <li>WhatsApp automated payment reminders and digital ledgers.</li>
  <li>100% tenant data privacy and multi-property management.</li>
</ul>
<p><strong><a href="/signup">Start Managing Your Properties Free on KirayaSaathi &rarr;</a></strong></p>
""",
},
    {
        "title": "How to Draft a Legally Enforceable Rent Agreement in India (11-Month Rule vs Registered Lease)",
        "slug": "legally-enforceable-rent-agreement-guide-india",
        "category": "Rent Laws & Agreements",
        "excerpt": "Understand why 11-month rental agreements are standard in India, when registration under the Registration Act 1908 is mandatory, state stamp duty costs, and essential landlord-protection clauses.",
        "cover_image": "https://images.unsplash.com/photo-1450133064473-71024230f91b?w=1200&auto=format&fit=crop&q=80",
        "author_name": "Gourav Berwal",
        "author_role": "Founder & Creator of KirayaSaathi",
        "read_time": "8 min read",
        "tags": "Rent Agreement, Indian Rental Laws, 11 Month Agreement, Police Verification, Stamp Duty",
        "is_featured": False,
        "is_published": False,
        "views_count": 0,
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
        "author_role": "Founder & Creator of KirayaSaathi",
        "read_time": "5 min read",
        "tags": "Tenant Screening, PG Verification, Tenant Background Check, Rental Safety",
        "is_featured": False,
        "is_published": False,
        "views_count": 0,
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
        "author_name": "Gourav Berwal",
        "author_role": "Founder & Creator of KirayaSaathi",
        "read_time": "7 min read",
        "tags": "Hostel Vacancy, PG Occupancy, Rental Business India, Student Housing, HRA Receipts",
        "is_featured": False,
        "is_published": False,
        "views_count": 0,
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

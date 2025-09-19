// PDF generation service for project management forms

interface EventProjectData {
  eventId: string
  eventTitle: string
  organization: string
  projectManager: string
  startDate: string
  endDate: string
  description: string
  objectives: string[]
  deliverables: string[]
  timeline: { milestone: string; date: string; status: 'pending' | 'in-progress' | 'completed' }[]
  team: { name: string; role: string; contact: string }[]
  budget: { item: string; amount: number; category: string }[]
  risks: { risk: string; probability: 'low' | 'medium' | 'high'; impact: 'low' | 'medium' | 'high'; mitigation: string }[]
  stakeholders: { name: string; role: string; influence: 'low' | 'medium' | 'high' }[]
}

class ProjectManagementPDFGenerator {
  // Generate a comprehensive project charter PDF
  static generateProjectCharter(eventData: EventProjectData): string {
    const content = this.generateProjectCharterContent(eventData)
    return this.createPDFDataURI(content, `Project_Charter_${eventData.eventId}.pdf`)
  }

  // Generate a project timeline/Gantt chart PDF
  static generateProjectTimeline(eventData: EventProjectData): string {
    const content = this.generateTimelineContent(eventData)
    return this.createPDFDataURI(content, `Project_Timeline_${eventData.eventId}.pdf`)
  }

  // Generate a risk assessment matrix PDF
  static generateRiskAssessment(eventData: EventProjectData): string {
    const content = this.generateRiskAssessmentContent(eventData)
    return this.createPDFDataURI(content, `Risk_Assessment_${eventData.eventId}.pdf`)
  }

  // Generate a resource allocation plan PDF
  static generateResourcePlan(eventData: EventProjectData): string {
    const content = this.generateResourcePlanContent(eventData)
    return this.createPDFDataURI(content, `Resource_Plan_${eventData.eventId}.pdf`)
  }

  // Generate a stakeholder communication plan PDF
  static generateCommunicationPlan(eventData: EventProjectData): string {
    const content = this.generateCommunicationContent(eventData)
    return this.createPDFDataURI(content, `Communication_Plan_${eventData.eventId}.pdf`)
  }

  // Generate project closure report template PDF
  static generateClosureReport(eventData: EventProjectData): string {
    const content = this.generateClosureReportContent(eventData)
    return this.createPDFDataURI(content, `Closure_Report_${eventData.eventId}.pdf`)
  }

  private static generateProjectCharterContent(data: EventProjectData): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Project Charter - ${data.eventTitle}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 18px; font-weight: bold; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 15px; }
        .field { margin-bottom: 10px; }
        .field-label { font-weight: bold; display: inline-block; width: 150px; }
        .field-value { display: inline-block; }
        .objectives-list { list-style-type: decimal; margin-left: 20px; }
        .team-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .team-table th, .team-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .team-table th { background-color: #f5f5f5; }
        .signature-section { margin-top: 50px; }
        .signature-box { display: inline-block; width: 300px; margin-right: 50px; }
        .signature-line { border-bottom: 1px solid #000; height: 40px; margin-bottom: 5px; }
        @media print { body { margin: 20px; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>PROJECT CHARTER</h1>
        <h2>${data.eventTitle}</h2>
        <p><strong>Organization:</strong> ${data.organization}</p>
        <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
    </div>

    <div class="section">
        <div class="section-title">Project Information</div>
        <div class="field">
            <span class="field-label">Project ID:</span>
            <span class="field-value">${data.eventId}</span>
        </div>
        <div class="field">
            <span class="field-label">Project Manager:</span>
            <span class="field-value">${data.projectManager}</span>
        </div>
        <div class="field">
            <span class="field-label">Start Date:</span>
            <span class="field-value">${data.startDate}</span>
        </div>
        <div class="field">
            <span class="field-label">End Date:</span>
            <span class="field-value">${data.endDate}</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Project Description</div>
        <p>${data.description}</p>
    </div>

    <div class="section">
        <div class="section-title">Project Objectives</div>
        <ol class="objectives-list">
            ${data.objectives.map(obj => `<li>${obj}</li>`).join('')}
        </ol>
    </div>

    <div class="section">
        <div class="section-title">Key Deliverables</div>
        <ul>
            ${data.deliverables.map(del => `<li>${del}</li>`).join('')}
        </ul>
    </div>

    <div class="section">
        <div class="section-title">Project Team</div>
        <table class="team-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Contact Information</th>
                </tr>
            </thead>
            <tbody>
                ${data.team.map(member => `
                    <tr>
                        <td>${member.name}</td>
                        <td>${member.role}</td>
                        <td>${member.contact}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    </div>

    <div class="signature-section">
        <h3>Approvals</h3>
        <div class="signature-box">
            <div class="signature-line"></div>
            <p><strong>Project Manager</strong><br>Date: ___________</p>
        </div>
        <div class="signature-box">
            <div class="signature-line"></div>
            <p><strong>Organization Director</strong><br>Date: ___________</p>
        </div>
    </div>
</body>
</html>`
  }

  private static generateTimelineContent(data: EventProjectData): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Project Timeline - ${data.eventTitle}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .timeline-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .timeline-table th, .timeline-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        .timeline-table th { background-color: #f5f5f5; font-weight: bold; }
        .status-pending { background-color: #fff3cd; }
        .status-in-progress { background-color: #d1ecf1; }
        .status-completed { background-color: #d4edda; }
        .gantt-chart { margin-top: 30px; }
        .gantt-row { display: flex; align-items: center; margin-bottom: 10px; }
        .gantt-label { width: 200px; font-size: 12px; }
        .gantt-bar { height: 20px; background-color: #007bff; margin-left: 10px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PROJECT TIMELINE</h1>
        <h2>${data.eventTitle}</h2>
        <p><strong>Organization:</strong> ${data.organization}</p>
        <p><strong>Project Period:</strong> ${data.startDate} to ${data.endDate}</p>
    </div>

    <h3>Project Milestones</h3>
    <table class="timeline-table">
        <thead>
            <tr>
                <th>Milestone</th>
                <th>Target Date</th>
                <th>Status</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            ${data.timeline.map(item => `
                <tr class="status-${item.status}">
                    <td>${item.milestone}</td>
                    <td>${item.date}</td>
                    <td>${item.status.toUpperCase()}</td>
                    <td>_______________________</td>
                </tr>
            `).join('')}
        </tbody>
    </table>

    <div class="gantt-chart">
        <h3>Visual Timeline</h3>
        <p><em>Use this section to draw or attach a visual Gantt chart representation</em></p>
        <div style="border: 1px dashed #ccc; height: 200px; display: flex; align-items: center; justify-content: center;">
            <p style="color: #666;">Gantt Chart Placeholder - Fill in manually or attach printed chart</p>
        </div>
    </div>

    <div style="margin-top: 40px;">
        <h3>Timeline Notes and Adjustments</h3>
        <div style="border: 1px solid #ddd; min-height: 150px; padding: 10px;">
            <p><em>Use this space to document timeline changes, delays, or accelerations:</em></p>
        </div>
    </div>
</body>
</html>`
  }

  private static generateRiskAssessmentContent(data: EventProjectData): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Risk Assessment - ${data.eventTitle}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .risk-table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }
        .risk-table th, .risk-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .risk-table th { background-color: #f5f5f5; font-weight: bold; }
        .risk-high { background-color: #f8d7da; }
        .risk-medium { background-color: #fff3cd; }
        .risk-low { background-color: #d4edda; }
        .risk-matrix { margin-top: 30px; }
        .matrix-table { border-collapse: collapse; margin: 20px auto; }
        .matrix-table td { width: 80px; height: 60px; border: 2px solid #333; text-align: center; vertical-align: middle; }
        .matrix-header { background-color: #f5f5f5; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>RISK ASSESSMENT MATRIX</h1>
        <h2>${data.eventTitle}</h2>
        <p><strong>Organization:</strong> ${data.organization}</p>
        <p><strong>Assessment Date:</strong> ${new Date().toLocaleDateString()}</p>
    </div>

    <h3>Identified Risks</h3>
    <table class="risk-table">
        <thead>
            <tr>
                <th style="width: 25%;">Risk Description</th>
                <th style="width: 12%;">Probability</th>
                <th style="width: 12%;">Impact</th>
                <th style="width: 12%;">Risk Level</th>
                <th style="width: 39%;">Mitigation Strategy</th>
            </tr>
        </thead>
        <tbody>
            ${data.risks.map(risk => {
              const riskLevel = this.calculateRiskLevel(risk.probability, risk.impact)
              return `
                <tr class="risk-${riskLevel}">
                    <td>${risk.risk}</td>
                    <td>${risk.probability.toUpperCase()}</td>
                    <td>${risk.impact.toUpperCase()}</td>
                    <td>${riskLevel.toUpperCase()}</td>
                    <td>${risk.mitigation}</td>
                </tr>
              `
            }).join('')}
        </tbody>
    </table>

    <div class="risk-matrix">
        <h3>Risk Probability/Impact Matrix</h3>
        <table class="matrix-table">
            <tr>
                <td class="matrix-header"></td>
                <td class="matrix-header">Low Impact</td>
                <td class="matrix-header">Medium Impact</td>
                <td class="matrix-header">High Impact</td>
            </tr>
            <tr>
                <td class="matrix-header">High Probability</td>
                <td class="risk-medium">MEDIUM</td>
                <td class="risk-high">HIGH</td>
                <td class="risk-high">HIGH</td>
            </tr>
            <tr>
                <td class="matrix-header">Medium Probability</td>
                <td class="risk-low">LOW</td>
                <td class="risk-medium">MEDIUM</td>
                <td class="risk-high">HIGH</td>
            </tr>
            <tr>
                <td class="matrix-header">Low Probability</td>
                <td class="risk-low">LOW</td>
                <td class="risk-low">LOW</td>
                <td class="risk-medium">MEDIUM</td>
            </tr>
        </table>
    </div>

    <div style="margin-top: 40px;">
        <h3>Risk Monitoring Plan</h3>
        <div style="border: 1px solid #ddd; min-height: 100px; padding: 10px;">
            <p><strong>Review Schedule:</strong> Weekly risk assessment during project execution</p>
            <p><strong>Escalation Procedures:</strong> High-risk items to be escalated to project sponsor within 24 hours</p>
            <p><strong>Additional Notes:</strong></p>
        </div>
    </div>
</body>
</html>`
  }

  private static generateResourcePlanContent(data: EventProjectData): string {
    const totalBudget = data.budget.reduce((sum, item) => sum + item.amount, 0)
    
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Resource Plan - ${data.eventTitle}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .resource-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .resource-table th, .resource-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        .resource-table th { background-color: #f5f5f5; font-weight: bold; }
        .total-row { background-color: #e9ecef; font-weight: bold; }
        .budget-summary { margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>RESOURCE ALLOCATION PLAN</h1>
        <h2>${data.eventTitle}</h2>
        <p><strong>Organization:</strong> ${data.organization}</p>
        <p><strong>Planning Date:</strong> ${new Date().toLocaleDateString()}</p>
    </div>

    <h3>Human Resources</h3>
    <table class="resource-table">
        <thead>
            <tr>
                <th>Team Member</th>
                <th>Role</th>
                <th>Allocation %</th>
                <th>Contact Information</th>
                <th>Start Date</th>
                <th>End Date</th>
            </tr>
        </thead>
        <tbody>
            ${data.team.map(member => `
                <tr>
                    <td>${member.name}</td>
                    <td>${member.role}</td>
                    <td>_____%</td>
                    <td>${member.contact}</td>
                    <td>__________</td>
                    <td>__________</td>
                </tr>
            `).join('')}
        </tbody>
    </table>

    <h3>Budget Allocation</h3>
    <table class="resource-table">
        <thead>
            <tr>
                <th>Budget Item</th>
                <th>Category</th>
                <th>Estimated Cost</th>
                <th>Actual Cost</th>
                <th>Variance</th>
            </tr>
        </thead>
        <tbody>
            ${data.budget.map(item => `
                <tr>
                    <td>${item.item}</td>
                    <td>${item.category}</td>
                    <td>$${item.amount.toFixed(2)}</td>
                    <td>$________</td>
                    <td>$________</td>
                </tr>
            `).join('')}
            <tr class="total-row">
                <td colspan="2"><strong>TOTAL</strong></td>
                <td><strong>$${totalBudget.toFixed(2)}</strong></td>
                <td><strong>$________</strong></td>
                <td><strong>$________</strong></td>
            </tr>
        </tbody>
    </table>

    <div class="budget-summary">
        <h3>Budget Summary</h3>
        <p><strong>Total Estimated Budget:</strong> $${totalBudget.toFixed(2)}</p>
        <p><strong>Contingency (10%):</strong> $${(totalBudget * 0.1).toFixed(2)}</p>
        <p><strong>Total with Contingency:</strong> $${(totalBudget * 1.1).toFixed(2)}</p>
    </div>

    <div style="margin-top: 40px;">
        <h3>Resource Procurement Plan</h3>
        <div style="border: 1px solid #ddd; min-height: 120px; padding: 10px;">
            <p><strong>Procurement Timeline:</strong></p>
            <p><strong>Vendor Selection Criteria:</strong></p>
            <p><strong>Approval Process:</strong></p>
            <p><strong>Additional Notes:</strong></p>
        </div>
    </div>
</body>
</html>`
  }

  private static generateCommunicationContent(data: EventProjectData): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Communication Plan - ${data.eventTitle}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .stakeholder-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .stakeholder-table th, .stakeholder-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        .stakeholder-table th { background-color: #f5f5f5; font-weight: bold; }
        .influence-high { background-color: #f8d7da; }
        .influence-medium { background-color: #fff3cd; }
        .influence-low { background-color: #d4edda; }
        .communication-matrix { margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>STAKEHOLDER COMMUNICATION PLAN</h1>
        <h2>${data.eventTitle}</h2>
        <p><strong>Organization:</strong> ${data.organization}</p>
        <p><strong>Plan Date:</strong> ${new Date().toLocaleDateString()}</p>
    </div>

    <h3>Stakeholder Analysis</h3>
    <table class="stakeholder-table">
        <thead>
            <tr>
                <th>Stakeholder</th>
                <th>Role/Interest</th>
                <th>Influence Level</th>
                <th>Communication Method</th>
                <th>Frequency</th>
            </tr>
        </thead>
        <tbody>
            ${data.stakeholders.map(stakeholder => `
                <tr class="influence-${stakeholder.influence}">
                    <td>${stakeholder.name}</td>
                    <td>${stakeholder.role}</td>
                    <td>${stakeholder.influence.toUpperCase()}</td>
                    <td>_________________</td>
                    <td>_________________</td>
                </tr>
            `).join('')}
        </tbody>
    </table>

    <div class="communication-matrix">
        <h3>Communication Matrix</h3>
        <table class="stakeholder-table">
            <thead>
                <tr>
                    <th>Information Type</th>
                    <th>Target Audience</th>
                    <th>Method</th>
                    <th>Frequency</th>
                    <th>Responsible Person</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Project Status Updates</td>
                    <td>All Stakeholders</td>
                    <td>Email, Website</td>
                    <td>Weekly</td>
                    <td>${data.projectManager}</td>
                </tr>
                <tr>
                    <td>Volunteer Recruitment</td>
                    <td>General Public</td>
                    <td>Social Media, Flyers</td>
                    <td>Ongoing</td>
                    <td>_________________</td>
                </tr>
                <tr>
                    <td>Safety Briefings</td>
                    <td>Volunteers</td>
                    <td>In-person, Email</td>
                    <td>Before Event</td>
                    <td>_________________</td>
                </tr>
                <tr>
                    <td>Financial Reports</td>
                    <td>Sponsors, Board</td>
                    <td>Formal Report</td>
                    <td>Monthly</td>
                    <td>_________________</td>
                </tr>
                <tr>
                    <td>Impact Results</td>
                    <td>All Stakeholders</td>
                    <td>Report, Presentation</td>
                    <td>Post-Event</td>
                    <td>_________________</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div style="margin-top: 40px;">
        <h3>Emergency Communication Procedures</h3>
        <div style="border: 1px solid #ddd; min-height: 100px; padding: 10px;">
            <p><strong>Emergency Contact:</strong> _________________</p>
            <p><strong>Escalation Chain:</strong> _________________</p>
            <p><strong>Media Contact Protocol:</strong> _________________</p>
            <p><strong>Crisis Communication Plan:</strong> _________________</p>
        </div>
    </div>
</body>
</html>`
  }

  private static generateClosureReportContent(data: EventProjectData): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Project Closure Report - ${data.eventTitle}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .section-title { font-size: 18px; font-weight: bold; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 15px; }
        .metrics-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .metrics-table th, .metrics-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        .metrics-table th { background-color: #f5f5f5; font-weight: bold; }
        .lessons-box { border: 1px solid #ddd; padding: 15px; margin-top: 15px; min-height: 100px; }
        .rating-scale { display: flex; justify-content: space-between; margin: 10px 0; }
        .rating-item { text-align: center; flex: 1; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PROJECT CLOSURE REPORT</h1>
        <h2>${data.eventTitle}</h2>
        <p><strong>Organization:</strong> ${data.organization}</p>
        <p><strong>Completion Date:</strong> ${new Date().toLocaleDateString()}</p>
    </div>

    <div class="section">
        <div class="section-title">Project Summary</div>
        <p><strong>Original Objectives:</strong></p>
        <ul>
            ${data.objectives.map(obj => `<li>${obj}</li>`).join('')}
        </ul>
        <p><strong>Final Outcomes:</strong> ______________________________________</p>
        <p><strong>Project Duration:</strong> ${data.startDate} to ${data.endDate}</p>
    </div>

    <div class="section">
        <div class="section-title">Performance Metrics</div>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Target</th>
                    <th>Actual</th>
                    <th>Variance</th>
                    <th>Comments</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Volunteers Recruited</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                </tr>
                <tr>
                    <td>Budget Performance</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                </tr>
                <tr>
                    <td>Timeline Performance</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                </tr>
                <tr>
                    <td>Quality Measures</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                </tr>
                <tr>
                    <td>Stakeholder Satisfaction</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                    <td>_______</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">Risk Management Effectiveness</div>
        <p>Rate the effectiveness of risk management (1 = Poor, 5 = Excellent):</p>
        <div class="rating-scale">
            <div class="rating-item">1 ☐</div>
            <div class="rating-item">2 ☐</div>
            <div class="rating-item">3 ☐</div>
            <div class="rating-item">4 ☐</div>
            <div class="rating-item">5 ☐</div>
        </div>
        <div class="lessons-box">
            <p><strong>Risk Management Comments:</strong></p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Lessons Learned</div>
        <div class="lessons-box">
            <p><strong>What Went Well:</strong></p>
        </div>
        <div class="lessons-box">
            <p><strong>What Could Be Improved:</strong></p>
        </div>
        <div class="lessons-box">
            <p><strong>Recommendations for Future Projects:</strong></p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Resource Utilization</div>
        <p><strong>Human Resources:</strong> _________________________________________________</p>
        <p><strong>Financial Resources:</strong> _________________________________________________</p>
        <p><strong>Material Resources:</strong> _________________________________________________</p>
        <p><strong>Technology Resources:</strong> _________________________________________________</p>
    </div>

    <div class="section">
        <div class="section-title">Project Closure Checklist</div>
        <p>☐ All deliverables completed and accepted</p>
        <p>☐ Final budget reconciliation completed</p>
        <p>☐ Volunteer feedback collected</p>
        <p>☐ Stakeholder satisfaction assessed</p>
        <p>☐ Project documentation archived</p>
        <p>☐ Equipment returned/disposed of</p>
        <p>☐ Team members debriefed</p>
        <p>☐ Impact measurement completed</p>
        <p>☐ Thank you communications sent</p>
        <p>☐ Lessons learned documented</p>
    </div>

    <div style="margin-top: 50px;">
        <p><strong>Project Manager Signature:</strong> _________________________ Date: _________</p>
        <p><strong>Organization Director Signature:</strong> _________________________ Date: _________</p>
    </div>
</body>
</html>`
  }

  private static calculateRiskLevel(probability: string, impact: string): string {
    const probMap = { low: 1, medium: 2, high: 3 }
    const impactMap = { low: 1, medium: 2, high: 3 }
    
    const score = probMap[probability as keyof typeof probMap] * impactMap[impact as keyof typeof impactMap]
    
    if (score <= 2) return 'low'
    if (score <= 4) return 'medium'
    return 'high'
  }

  private static createPDFDataURI(content: string, filename: string): string {
    // Create a blob with the HTML content
    const blob = new Blob([content], { type: 'text/html' })
    
    // Create a data URI for download
    const url = URL.createObjectURL(blob)
    
    // Create download link and trigger download
    const a = document.createElement('a')
    a.href = url
    a.download = filename.replace('.pdf', '.html') // HTML format for now
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    return url
  }
}

export { ProjectManagementPDFGenerator, type EventProjectData }
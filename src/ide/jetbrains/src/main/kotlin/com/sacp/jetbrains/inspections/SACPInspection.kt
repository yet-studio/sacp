package com.sacp.jetbrains.inspections

import com.intellij.codeInspection.*
import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.psi.PsiElementVisitor
import com.intellij.psi.PsiFile
import com.sacp.jetbrains.services.SACPService

class SACPInspection : LocalInspectionTool() {
    override fun buildVisitor(holder: ProblemsHolder, isOnTheFly: Boolean): PsiElementVisitor {
        return object : PsiElementVisitor() {
            override fun visitFile(file: PsiFile) {
                if (file.virtualFile?.extension != "py") return

                val project = file.project
                val service = project.service<SACPService>()
                
                // Get diagnostics from LSP
                val diagnostics = service.getVerificationResults()
                
                // Convert diagnostics to problems
                for (diagnostic in diagnostics) {
                    val range = diagnostic.range
                    val startOffset = getOffset(file, range.start.line, range.start.character)
                    val endOffset = getOffset(file, range.end.line, range.end.character)
                    
                    if (startOffset != null && endOffset != null) {
                        holder.registerProblem(
                            file,
                            TextRange(startOffset, endOffset),
                            diagnostic.message,
                            when (diagnostic.severity) {
                                1 -> ProblemHighlightType.ERROR
                                2 -> ProblemHighlightType.WARNING
                                3 -> ProblemHighlightType.WEAK_WARNING
                                else -> ProblemHighlightType.INFORMATION
                            },
                            *createQuickFixes(diagnostic).toTypedArray()
                        )
                    }
                }
            }
        }
    }

    private fun getOffset(file: PsiFile, line: Int, character: Int): Int? {
        val document = file.viewProvider.document ?: return null
        return try {
            document.getLineStartOffset(line) + character
        } catch (e: Exception) {
            null
        }
    }

    private fun createQuickFixes(diagnostic: org.eclipse.lsp4j.Diagnostic): List<LocalQuickFix> {
        val fixes = mutableListOf<LocalQuickFix>()
        
        // Add quick fixes based on diagnostic type
        when (diagnostic.source) {
            "SACP.COMPLIANCE" -> fixes.add(ComplianceQuickFix())
            "SACP.BEHAVIOR" -> fixes.add(BehaviorQuickFix())
            "SACP.VERIFICATION" -> fixes.add(VerificationQuickFix())
        }
        
        return fixes
    }
}

class ComplianceQuickFix : LocalQuickFix {
    override fun getName() = "Fix compliance issue"
    override fun getFamilyName() = name
    
    override fun applyFix(project: Project, descriptor: ProblemDescriptor) {
        // Apply compliance fix
    }
}

class BehaviorQuickFix : LocalQuickFix {
    override fun getName() = "Fix behavior issue"
    override fun getFamilyName() = name
    
    override fun applyFix(project: Project, descriptor: ProblemDescriptor) {
        // Apply behavior fix
    }
}

class VerificationQuickFix : LocalQuickFix {
    override fun getName() = "Fix verification issue"
    override fun getFamilyName() = name
    
    override fun applyFix(project: Project, descriptor: ProblemDescriptor) {
        // Apply verification fix
    }
}

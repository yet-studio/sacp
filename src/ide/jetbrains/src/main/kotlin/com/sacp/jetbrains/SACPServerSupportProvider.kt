package com.sacp.jetbrains

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.platform.lsp.api.LspServerSupportProvider
import com.intellij.platform.lsp.api.ProjectWideLspServerDescriptor

class SACPServerSupportProvider : LspServerSupportProvider {
    override fun fileOpened(project: Project, file: VirtualFile, serverStarter: LspServerSupportProvider.LspServerStarter) {
        if (file.extension == "py") {
            serverStarter.ensureServerStarted(SACPServerDescriptor(project))
        }
    }
}

private class SACPServerDescriptor(project: Project) : ProjectWideLspServerDescriptor(project, "SACP") {
    override fun createCommandLine(): GeneralCommandLine {
        return GeneralCommandLine().apply {
            exePath = "python"
            addParameter("-m")
            addParameter("sacp.ide.lsp_server")
        }
    }

    override fun isSupportedFile(file: VirtualFile) = file.extension == "py"
}

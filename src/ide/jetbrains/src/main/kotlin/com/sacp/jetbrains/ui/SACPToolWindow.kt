package com.sacp.jetbrains.ui

import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.content.ContentFactory
import com.intellij.ui.table.JBTable
import com.sacp.jetbrains.services.SACPService
import javax.swing.table.AbstractTableModel
import javax.swing.table.DefaultTableModel

class SACPToolWindowFactory : ToolWindowFactory {
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val sacpToolWindow = SACPToolWindow(project)
        val content = ContentFactory.getInstance().createContent(sacpToolWindow.content, "", false)
        toolWindow.contentManager.addContent(content)
    }
}

class SACPToolWindow(private val project: Project) {
    val content = JBScrollPane(createMainPanel())

    private fun createMainPanel(): JBTable {
        val table = JBTable()
        table.model = createTableModel()
        return table
    }

    private fun createTableModel(): AbstractTableModel {
        return object : DefaultTableModel() {
            private val columnNames = arrayOf("Type", "Message", "File", "Line")
            private val data = project.service<SACPService>().getVerificationResults().map { diagnostic ->
                arrayOf(
                    diagnostic.source,
                    diagnostic.message,
                    diagnostic.range.start.line,
                    diagnostic.range.start.character
                )
            }.toTypedArray()

            override fun getColumnName(column: Int): String = columnNames[column]
            override fun getRowCount(): Int = data.size
            override fun getColumnCount(): Int = columnNames.size
            override fun getValueAt(row: Int, col: Int): Any = data[row][col]
            override fun isCellEditable(row: Int, column: Int): Boolean = false
        }
    }
}

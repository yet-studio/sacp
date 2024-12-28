"""
SafeAI CodeGuard Protocol - Team Collaboration Module
Implements team management, roles, and collaboration features.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto
from datetime import datetime
import uuid

class Role(Enum):
    """Team member roles"""
    VIEWER = auto()          # Can only view code and reports
    CONTRIBUTOR = auto()     # Can suggest changes and create PRs
    REVIEWER = auto()        # Can review and approve changes
    ADMIN = auto()          # Full team management access
    OWNER = auto()          # Organization-level control

@dataclass
class TeamMember:
    """Represents a team member"""
    id: str
    name: str
    email: str
    role: Role
    teams: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

@dataclass
class Team:
    """Represents a team"""
    id: str
    name: str
    description: str
    members: Dict[str, TeamMember] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

class TeamManager:
    """Manages teams and their members"""
    
    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.members: Dict[str, TeamMember] = {}
    
    def create_team(self, name: str, description: str) -> Team:
        """Create a new team"""
        team_id = str(uuid.uuid4())
        team = Team(id=team_id, name=name, description=description)
        self.teams[team_id] = team
        return team
    
    def add_member(self, team_id: str, member: TeamMember) -> bool:
        """Add a member to a team"""
        if team_id not in self.teams:
            return False
        
        team = self.teams[team_id]
        team.members[member.id] = member
        member.teams.add(team_id)
        self.members[member.id] = member
        return True
    
    def remove_member(self, team_id: str, member_id: str) -> bool:
        """Remove a member from a team"""
        if team_id not in self.teams or member_id not in self.members:
            return False
        
        team = self.teams[team_id]
        member = self.members[member_id]
        
        if member_id in team.members:
            del team.members[member_id]
            member.teams.remove(team_id)
            return True
        return False
    
    def update_member_role(self, member_id: str, new_role: Role) -> bool:
        """Update a member's role"""
        if member_id not in self.members:
            return False
        
        member = self.members[member_id]
        member.role = new_role
        return True
    
    def get_team_members(self, team_id: str) -> List[TeamMember]:
        """Get all members of a team"""
        if team_id not in self.teams:
            return []
        return list(self.teams[team_id].members.values())
    
    def get_member_teams(self, member_id: str) -> List[Team]:
        """Get all teams a member belongs to"""
        if member_id not in self.members:
            return []
        
        member = self.members[member_id]
        return [self.teams[team_id] for team_id in member.teams]
    
    def check_permission(self, member_id: str, required_role: Role) -> bool:
        """Check if a member has the required role level"""
        if member_id not in self.members:
            return False
        
        member = self.members[member_id]
        return member.role.value >= required_role.value

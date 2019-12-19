from .etc import *

class CircPolicyMatrices(list):
    def __init__(self, circ_policy_group):
        sql = '''
            select distinct ct.circ_policy_matrix_id
            from circ_transactions ct
            join circ_policy_matrix cpm
              on ct.circ_policy_matrix_id = cpm.circ_policy_matrix_id
            where cpm.circ_group_id = :cpg
            order by ct.circ_policy_matrix_id
        '''
        self += [row[0] for row in
                 run(sql, cpg=circ_policy_group)]

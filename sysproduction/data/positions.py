from syscore.objects import arg_not_supplied, missing_data, success, failure

from sysproduction.data.contracts import missing_contract
from sysproduction.data.get_data import dataBlob


class diagPositions(object):
    def __init__(self, data = arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoRollStateData mongoContractPositionData mongoStrategyPositionData")
        self.data = data

    def get_roll_state(self, instrument_code):
        return self.data.mongo_roll_state.get_roll_state(instrument_code)

    def get_positions_for_instrument_and_contract_list(self, instrument_code, contract_list):
        list_of_positions = [self.get_position_for_instrument_and_contract_date(instrument_code, contract_date)
                             for contract_date in contract_list]

        return list_of_positions

    def get_position_for_instrument_and_contract_date(self, instrument_code, contract_date):
        if contract_date is missing_contract:
            return 0.0
        position = self.data.mongo_contract_position.\
                get_current_position_for_instrument_and_contract_date(instrument_code, contract_date)
        if position is missing_data:
            return 0.0

        return position.position

    def get_position_for_strategy_and_instrument(self, strategy_name, instrument_code):
        position = self.data.mongo_strategy_position.get_current_position_for_strategy_and_instrument(strategy_name, instrument_code)
        if position is missing_data:
            return 0.0
        return position.position

    def get_list_of_instruments_for_strategy_with_position(self, strategy_name):
        instrument_list = self.data.mongo_strategy_position.get_list_of_instruments_for_strategy_with_position(strategy_name)
        return instrument_list

    def get_list_of_instruments_with_any_position(self):
        return self.data.mongo_contract_position.get_list_of_instruments_with_any_position()

class updatePositions(object):
    def __init__(self, data = arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoContractPositionData mongoStrategyPositionData")
        self.data = data

    def update_strategy_position_table_with_instrument_order(self, instrument_order):
        """
        Alter the strategy position table according to instrument order fill value

        :param instrument_order:
        :return:
        """

        strategy_name = instrument_order.strategy_name
        instrument_code = instrument_order.instrument_code
        current_position = self.data.mongo_strategy_position.\
            get_current_position_for_strategy_and_instrument(strategy_name, instrument_code)
        trade_done = instrument_order.fill
        new_position = current_position + trade_done

        self.data.mongo_strategy_position.\
            update_position_for_strategy_and_instrument(strategy_name, instrument_code, new_position)

        self.log.msg("Updated position of %s/%s from %d to %d because of trade %s %d" %
                     (strategy_name, instrument_code, current_position, new_position, str(instrument_order),
                      instrument_order.order_id))

        return success

    def update_contract_position_table_with_contract_order(self, contract_order):
        """
        Alter the strategy position table according to contract order fill value

        :param contract_order:
        :return:
        """

        instrument_code = contract_order.instrument_code
        contract_id_list = contract_order.contract_id
        fill_list = contract_order.fill

        for trade_done, contract_id in zip(fill_list, contract_id_list):
            current_position = self.data.mongo_contract_position.\
                get_current_position_for_instrument_and_contract_date(instrument_code, contract_id)
            new_position = current_position + trade_done

            self.data.mongo_contract_position.\
                update_position_for_instrument_and_contract_date(instrument_code, contract_id, new_position)

            self.log.msg("Updated position of %s/%s from %d to %d because of trade %s %d" %
                         (instrument_code, contract_id, current_position, new_position, str(contract_order),
                          contract_order.order_id))

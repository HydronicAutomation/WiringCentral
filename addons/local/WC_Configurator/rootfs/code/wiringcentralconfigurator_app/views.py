import datetime
import json
import os
import random
import time

from django.conf import settings
from django.shortcuts import render
from django.views.generic.edit import CreateView, FormView
from django.views.generic import TemplateView
from django.urls import reverse_lazy, reverse
from django.http.response import HttpResponseRedirect, JsonResponse
from django.contrib import messages

from .forms import TokenAddEditForm, ConfigurationForm, SensorConfigurationForm, RelayConfigurationForm, \
    ConfigurationMasterSlaveForm, ConfigurationDefaultRuleFormSet, ConfigurationMasterSlaveFormSet
from .models import LongLivedAccessToken
from .api_client import get_boards, get_board_details, post_board_configuration, get_board_configuration, \
    post_board_sensor_configuration, get_board_sensor_configuration, get_board_relay_configuration, \
    post_board_relay_configuration, get_relay_entities, get_relay_entity_details, get_board_masterslave_configuration, \
    post_board_masterslave_configuration, get_board_defaultrule_configuration, post_board_default_rule_configuration


# Create your views here.


class RedirectView(TemplateView):
    template_name = 'wiringcentralconfigurator_app/list_boards.html'

    def get(self, request, *args, **kwargs):
        token_obj = LongLivedAccessToken.objects.first()
        if os.getenv("SUPERVISOR_TOKEN") is not None:
            if not settings.FULL_ACCESS:
                return HttpResponseRedirect(reverse_lazy('list_board_minimal_view'))
            return HttpResponseRedirect(reverse_lazy('list_board_view'))
        if token_obj is None:
            print("No token - Redirecting to access token view")
            messages.info(self.request, 'Add token to proceed', fail_silently=True)
            return HttpResponseRedirect(reverse_lazy('save_access_token_view'))
        else:
            try:
                status, data = get_boards(token_obj.token)
                if status is False:
                    if data.find('401') >= 0:
                        messages.info(self.request, 'Saved Token is invalid', fail_silently=True)
                        print("Token invalid, Redirecting to access token view")
                        return HttpResponseRedirect(reverse_lazy('save_access_token_view'))
            except:
                messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
                # return HttpResponseRedirect(reverse_lazy('save_access_token_view'))

        if not settings.FULL_ACCESS:
            return HttpResponseRedirect(reverse_lazy('list_board_minimal_view'))
        return HttpResponseRedirect(reverse_lazy('list_board_view'))


class SaveLongLivedAccessTokenView(FormView):
    template_name = 'wiringcentralconfigurator_app/create_access_token.html'
    form_class = TokenAddEditForm
    success_url = reverse_lazy('save_access_token_view')

    def get(self, request, *args, **kwargs):
        print("On SaveLongLivedAccessTokenView")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token_obj = LongLivedAccessToken.objects.first()
        if token_obj is not None:
            context["token"] = token_obj.token
        return context

    # def get_initial(self):
    #     initial = super().get_initial()
    #     token_obj = LongLivedAccessToken.objects.first()
    #     if token_obj is not None:
    #         initial["token"] = token_obj.token
    #     return initial

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get("token")
            print("saving token ", token)
            token_obj = LongLivedAccessToken.objects.first()
            if token_obj is None:
                token_obj = LongLivedAccessToken()
            token_obj.token = token
            token_obj.save()
            return HttpResponseRedirect(reverse_lazy('redirect_view'))
        return super().post(request, *args, **kwargs)


class ListBoardView(TemplateView):
    template_name = 'wiringcentralconfigurator_app/list_boards.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        token_obj = LongLivedAccessToken.objects.first()
        if token_obj is not None:
            try:
                board_obj = get_boards(token_obj.token)
                if board_obj[0]:
                    print(board_obj)
                    context['board_list'] = board_obj[1]
            except:
                messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        # context['board_list'] = ['WC-1234567']
        return context


class ListBoardMinimalView(TemplateView):
    template_name = 'wiringcentralconfigurator_app/list_boards_minimal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        token_obj = LongLivedAccessToken.objects.first()
        if token_obj is not None:
            try:
                board_obj = get_boards(token_obj.token)
                if board_obj[0]:
                    print(board_obj)
                    context['board_list'] = board_obj[1]
            except:
                messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        # context['board_list'] = ['WC-1234567']
        return context


class ConfigurationThermostatView(FormView):
    template_name = 'wiringcentralconfigurator_app/wc_sensor_configurator.html'
    form_class = ConfigurationForm
    success_url = reverse_lazy('list_board_view')

    def get_kwargs(self):
        return self.kwargs.get('board')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        token_obj = LongLivedAccessToken.objects.first()
        board_name = self.kwargs.get('board')
        context['entity_name'] = board_name
        context['form'] = self.form_class(
            initial={"name_{}".format(num): "{}-{}".format(board_name, num) for num in range(0, 9)})
        if self.kwargs.get('board') is not None:
            if token_obj is not None and board_name is not None:
                try:
                    status, board_data = get_board_configuration(token_obj.token, board_name)
                    print(status, board_data)
                    if status:
                        # try:
                        #     board_data = json.loads(board_data)
                        # except Exception as e:
                        #     print("Exception {}".format(e))
                        #     messages.info(self.request, 'No previous configuration found.', fail_silently=True)
                        #     return context
                        initial = {}
                        if len(board_data) == 0:
                            messages.info(self.request, 'No previous configuration found.', fail_silently=True)
                            context['thermostatID'] = board_name
                            # populate the form with default values
                            for i in range(1,9):
                                initial['name_{}'.format(i)] = "{}-{}".format(board_name, i)
                                initial['type_{}'.format(i)] = 'NTC'
                                initial['feed_{}'.format(i)] = f"{i}"
                                initial['multiplier_{}'.format(i)] = 1.0
                                initial['summer_{}'.format(i)] = 0.0
                                context['form'] = self.form_class(initial=initial)
                            return context

                        num = 1
                        for data in board_data:
                            initial['name_{}'.format(num)] = data['name']
                            initial['type_{}'.format(num)] = data['type']
                            initial['feed_{}'.format(num)] = data['feed']
                            initial['multiplier_{}'.format(num)] = data.get('multiplier', 1.0)
                            initial['summer_{}'.format(num)] = data.get('summer', 0.0)
                            num += 1
                        # print(initial)
                        context['form'] = self.form_class(initial=initial)
                    board_obj = get_board_details(token_obj.token, self.get_kwargs())
                    if board_obj[0]:
                        # print(board_obj)
                        context['thermostatID'] = board_name
                except Exception as e:
                    print("Exception, {}".format(e))
                    messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return context

    def form_valid(self, form):
        datas = []
        board_name = self.kwargs.get('board')
        if self.request.method == "POST":
            form = self.form_class(self.request.POST)
            if form.is_valid():
                for num in range(1, 9):
                    datas.append({
                        "name": form.cleaned_data['name_{}'.format(num)],
                        "type": form.cleaned_data['type_{}'.format(num)],
                        "feed": form.cleaned_data['feed_{}'.format(num)],
                        "multiplier": form.cleaned_data['multiplier_{}'.format(num)],
                        "summer": form.cleaned_data['summer_{}'.format(num)],
                                  })
                token_obj = LongLivedAccessToken.objects.first()
                if token_obj is not None and self.get_kwargs() is not None:
                    try:
                        status, message =post_board_configuration(token_obj.token, board_id=board_name, data=datas)
                        if not status:
                            messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
                            return HttpResponseRedirect(reverse_lazy('configuration_thermostat_view', kwargs={"board": board_name}))
                        messages.success(self.request, 'Configuration saved, restart HA to view changes!', fail_silently=True)
                        return HttpResponseRedirect(self.success_url)
                    except Exception as e:
                        print("Exception: {}".format(e))
                        messages.error(self.request, 'Home Assistant not responding, {}'.format(e), fail_silently=True)
        return super().form_invalid(form)


def configuration_ajax_view(request):
    data = {}
    board_detail_list = []
    if request.is_ajax() and request.method == 'GET':
        token_obj = LongLivedAccessToken.objects.first()
        board_name = request.GET.get('board')
        if board_name is not None:
            if token_obj is not None:
                try:
                    board_obj = get_board_details(token_obj.token, board_name)
                    print(board_obj)
                    if board_obj[0]:
                        for board_details in board_obj[1]:
                            if 'TYPE' in board_details and (board_details['TYPE'] == 'DS18B20' or board_details['TYPE'] == 'SHTC3-TEMP'):
                                board_detail_list.append(board_details)
                except:
                    messages.error(request, 'Home Assistant not responding', fail_silently=True)
    data['board_details_count'] = len(board_detail_list)
    data['board_details'] = board_detail_list
    return JsonResponse(data=data)


def configuration_relay_ajax_view(request):
    data = {}
    board_detail_list = []
    if request.is_ajax() and request.method == 'GET':
        token_obj = LongLivedAccessToken.objects.first()
        board_name = request.GET.get('board')
        if board_name is not None:
            if token_obj is not None:
                try:
                    # board_obj = get_relay_entities(token_obj.token)
                    board_obj = get_relay_entity_details(token_obj.token)
                    print(board_obj)
                    if board_obj[0]:
                        for board_details in board_obj[1]:
                            if 'TYPE' in board_details and board_details['TYPE'] == 'RELAY':
                                board_detail_list.append(board_details)
                except Exception as e:
                    print("Exception occured ", e)
                    messages.error(request, 'Home Assistant not responding', fail_silently=True)
    data['board_details_count'] = len(board_detail_list)
    data['board_details'] = board_detail_list
    return JsonResponse(data=data)


class ConfigurationSensorView(FormView):
    template_name = 'wiringcentralconfigurator_app/wc_sensor_enable.html'
    form_class = SensorConfigurationForm
    success_url = reverse_lazy('list_board_view')

    def get_kwargs(self):
        return self.kwargs.get('board')

    def get_board_obj(self):
        token_obj = LongLivedAccessToken.objects.first()
        board_name = self.get_kwargs()
        DS18B20_list = []
        if board_name is not None:
            if token_obj is not None:
                try:
                    board_obj = get_board_details(token_obj.token, board_name)
                    if board_obj[0]:
                        for board_details in board_obj[1]:
                            if 'TYPE' in board_details and board_details['TYPE'] == 'DS18B20':
                                DS18B20_list.append(f'{board_details["SENSOR"]}')
                except:
                    messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return DS18B20_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        board_name = self.get_kwargs()
        context['form'] = self.form_class
        DS18B20_kwargs={}
        for field in self.get_board_obj():
            DS18B20_kwargs[field] = True
        context['DS18B20_kwargs'] = DS18B20_kwargs
        token_obj = LongLivedAccessToken.objects.first()
        if token_obj is not None and board_name is not None:
            context['entity_name'] = board_name
            try:
                status, sensor_data = get_board_sensor_configuration(token_obj.token, board_name)
                if status:
                    initial = {}
                    num = 1
                    for data in sensor_data:
                        if data['type'] == "NTC":
                            initial['ntc_{}'.format(data['feed'])] = data['enabled']
                        elif data['type'] == "DS18B20":
                            if DS18B20_kwargs.get(data['feed']) is not None:
                                DS18B20_kwargs[data['feed']] = data['enabled']
                        else:
                            pass
                        num += 1
                    context['form'] = self.form_class(initial=initial)
            except:
                messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return context

    def form_valid(self, form):
        datas = []
        board_name = self.get_kwargs()
        if self.request.method == "POST":
            form = self.form_class(self.request.POST)
            if form.is_valid():
                for key in form.fields.keys():
                    # print(key, form.cleaned_data[key])
                    datas.append({"type": "NTC", "feed": key[-1], "enabled": form.cleaned_data[key]})
                for field in self.get_board_obj():
                    if field in self.request.POST:
                        datas.append({"type": "DS18B20", "feed": field, "enabled": True})
                    else:
                        datas.append({"type": "DS18B20", "feed": field, "enabled": False})
        token_obj = LongLivedAccessToken.objects.first()
        if token_obj is not None and self.get_kwargs() is not None:
            try:
                status, message = post_board_sensor_configuration(token_obj.token, board_id=self.get_kwargs(), data=datas)
                if not status:
                    messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
                    return HttpResponseRedirect(reverse_lazy('configuration_sensor_view', kwargs={"board": board_name}))
                messages.success(self.request, 'Configuration saved', fail_silently=True)

                return HttpResponseRedirect(self.success_url)
            except:
                messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return super().form_valid(form)


class ConfigurationRelayView(FormView):
    template_name = 'wiringcentralconfigurator_app/wc_relay_configurator.html'
    form_class = RelayConfigurationForm
    success_url = reverse_lazy('list_board_view')

    def get_kwargs(self):
        return self.kwargs.get('board')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        token_obj = LongLivedAccessToken.objects.first()
        board_name = self.kwargs.get('board')
        context['entity_name'] = board_name
        context['form'] = self.form_class(
            initial={"name_{}".format(num): "{}-{}".format(board_name, num) for num in range(0, 9)})
        if self.kwargs.get('board') is not None:
            if token_obj is not None and board_name is not None:
                try:
                    status, board_data = get_board_relay_configuration(token_obj.token, board_name)
                    print(status, board_data)
                    if status:
                        # try:
                        #     board_data = json.loads(board_data)
                        # except Exception as e:
                        #     print("Exception {}".format(e))
                        #     messages.info(self.request, 'No previous configuration found.', fail_silently=True)
                        #     return context
                        initial = {}
                        if len(board_data) == 0:
                            messages.info(self.request, 'No previous configuration found.', fail_silently=True)
                            context['thermostatID'] = board_name
                            return context

                        num = 1
                        for data in board_data:
                            initial['name_{}'.format(num)] = data['name']
                            initial['type_{}'.format(num)] = data['type']
                            initial['feed_{}'.format(num)] = data['feed']
                            num += 1
                        # print(initial)
                        context['form'] = self.form_class(initial=initial)
                    board_obj = get_board_details(token_obj.token, self.get_kwargs())
                    if board_obj[0]:
                        # print(board_obj)
                        context['thermostatID'] = board_name
                except Exception as e:
                    print("Exception, {}".format(e))
                    messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return context

    def form_valid(self, form):
        datas = []
        board_name = self.kwargs.get('board')
        if self.request.method == "POST":
            form = self.form_class(self.request.POST)
            if form.is_valid():
                for num in range(1, 9):
                    datas.append({"name": form.cleaned_data['name_{}'.format(num)],
                                  "type": form.cleaned_data['type_{}'.format(num)],
                                  "feed": form.cleaned_data['feed_{}'.format(num)]})
                token_obj = LongLivedAccessToken.objects.first()
                if token_obj is not None and self.get_kwargs() is not None:
                    try:
                        status, message =post_board_relay_configuration(token_obj.token, board_id=board_name, data=datas)
                        if not status:
                            messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
                            return HttpResponseRedirect(reverse_lazy('configuration_relay_view', kwargs={"board": board_name}))
                        messages.success(self.request, 'Configuration saved, restart HA to view changes!', fail_silently=True)
                        return HttpResponseRedirect(self.success_url)
                    except Exception as e:
                        print("Exception: {}".format(e))
                        messages.error(self.request, 'Home Assistant not responding, {}'.format(e), fail_silently=True)
        return super().form_invalid(form)


class ConfigurationOptionsView(TemplateView):
    template_name = 'wiringcentralconfigurator_app/wc_configuration_select.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        board_name = self.kwargs.get('board')
        context['entity_name'] = board_name
        context['thermostatID'] = board_name
        context['full_access'] = settings.FULL_ACCESS
        return context


class ConfigurationMasterSlaveView(FormView):
    template_name = 'wiringcentralconfigurator_app/wc_master_slave_configurator.html'
    form_class = ConfigurationMasterSlaveFormSet
    # success_url = reverse_lazy('list_board_view')

    def get_success_url(self):
        return reverse('configuration_masterslave_view', kwargs={'board': self.kwargs.get('board')})

    def get_kwargs(self):
        kwargs = self.kwargs.get('board')
        return kwargs

    def get_form_kwargs(self):
        print("get_form_kwargs")
        kwargs = super().get_form_kwargs()
        # print("kwargs", kwargs)
        # board_name = self.kwargs.get('board')
        # board_choices = [("NO FOLLOW", "NO FOLLOW")]
        # session_choice = self.request.session.get('board_choices')
        # for num in range(1, 9):
        #     board_choices.append(("{}-{}".format(board_name, num), "{}-{}".format(board_name, num)))
        # kwargs["board_choices"] = session_choice or board_choices
        return kwargs

    def get_initial(self):
        print("get_initial")
        initial = super().get_initial()
        # board_name = self.kwargs.get('board')
        # for num in range(1, 9):
        #     initial["name_{}".format(num)] = "{}-{}".format(board_name, num)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        print('get_context_data')

        token_obj = LongLivedAccessToken.objects.first()
        board_name = self.kwargs.get('board')
        context['entity_name'] = board_name
        context['thermostatID'] = board_name
        if self.kwargs.get('board') is not None:
            if token_obj is not None and board_name is not None:
                try:
                    # Read the current masterslave config
                    status, board_data = get_board_masterslave_configuration(token_obj.token, board_name)
                    print("status, board_data", status, board_data)
                    # status = True
                    # board_data = [{'name': 'WC-12345678-1', 'master': 'WC-12345678-1'}, {'name': 'WC-12345678-2', 'master': 'WC-12345678-2'}, {'name': 'WC-12345678-3', 'master': 'WC-12345678-3'}, {'name': 'WC-12345678-4', 'master': 'WC-12345678-4'}, {'name': 'WC-12345678-5', 'master': 'WC-12345678-5'}, {'name': 'WC-12345678-6', 'master': 'WC-12345678-6'}, {'name': 'WC-12345678-7', 'master': 'WC-12345678-7'}, {'name': 'WC-12345678-8', 'master': 'WC-12345678-8'}]

                    if status:
                        initial = []
                        if len(board_data) == 0:
                            messages.info(self.request, 'No masterslave configuration found.', fail_silently=True)
                            context['thermostatID'] = board_name
                            return context

                        board_choices = [("NO FOLLOW", "NO FOLLOW")]
                        for data in board_data:
                            initial.append({
                                'name': data['object_id'],
                                'type': data['master_object_id'] or 'NO FOLLOW'
                            })
                            board_choices.append(("{}".format(data['object_id']), "{}".format(data['object_id'])))
                            self.request.session['board_choices'] = board_choices

                        print(initial)
                        context['form'] = self.form_class(initial=initial, form_kwargs={'board_choices': board_choices})
                    else:
                        messages.error(self.request, 'Cannot get masterslave configuration', fail_silently=True)
                except Exception as e:
                    print("Exception, {}".format(e))
                    messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return context

    def post(self, request, *args, **kwargs):
        board_name = self.kwargs.get('board')
        board_choices = self.request.session.get('board_choices')
        form = self.form_class(self.request.POST, form_kwargs={'board_choices': board_choices})
        datas = []
        if form.is_valid():
            for iform in form:
                print(iform.cleaned_data)
                datas.append({
                    'object_id': iform.cleaned_data['name'],
                    'master_object_id': None if iform.cleaned_data['type'] == 'NO FOLLOW' else iform.cleaned_data[
                        'type']
                })

            print("=======")
            print(datas)

            token_obj = LongLivedAccessToken.objects.first()
            if token_obj is not None and self.get_kwargs() is not None:
                pass
                try:
                    # Post the new master slave config
                    status, message = post_board_masterslave_configuration(token_obj.token, board_id=board_name,
                                                                           data=datas)
                    if not status:
                        messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
                        return HttpResponseRedirect(
                            reverse_lazy('configuration_masterslave_view', kwargs={"board": board_name}))
                    messages.success(self.request, 'Master/Slave Configuration applied successfully!',
                                     fail_silently=True)
                    return HttpResponseRedirect(self.get_success_url())
                except Exception as e:
                    print("Exception: {}".format(e))
                    messages.error(self.request, 'Home Assistant not responding, {}'.format(e), fail_silently=True)
        messages.error(self.request, 'Error occured: {}'.format("Form is Invalid"), fail_silently=True)
        return HttpResponseRedirect(
            reverse_lazy('configuration_masterslave_view', kwargs={"board": board_name}))

    # def form_invalid(self, form):
    #     print("form invalid")
    #     print(form.errors)
    #     return super().form_invalid(form)


    # def form_valid(self, form):
    #     datas = []
    #     board_name = self.kwargs.get('board')
    #     if self.request.method == "POST":
    #         # board_choices = [("NO FOLLOW", "NO FOLLOW")]
    #         # for num in range(0, 9):
    #         #     board_choices.append(("{}-{}".format(board_name, num), "{}-{}".format(board_name, num)))
    #         # form = self.form_class(self.request.POST, form_kwargs={'board_choices': board_choices})
    #         if form.is_valid():
    #             for iform in form:
    #                 print(iform.cleaned_data)
    #                 datas.append({
    #                     'object_id': iform.cleaned_data['name'],
    #                     'master_object_id': None if iform.cleaned_data['type'] == 'NO FOLLOW' else iform.cleaned_data['type']
    #                 })
    #
    #             print("=======")
    #             print(datas)
    #
    #             token_obj = LongLivedAccessToken.objects.first()
    #             if token_obj is not None and self.get_kwargs() is not None:
    #                 pass
    #                 try:
    #                     # Post the new master slave config
    #                     status, message = post_board_masterslave_configuration(token_obj.token, board_id=board_name, data=datas)
    #                     if not status:
    #                         messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
    #                         return HttpResponseRedirect(reverse_lazy('configuration_masterslave_view', kwargs={"board": board_name}))
    #                     messages.success(self.request, 'Master/Slave Configuration applied successfully!', fail_silently=True)
    #                     return HttpResponseRedirect(self.success_url)
    #                 except Exception as e:
    #                     print("Exception: {}".format(e))
    #                     messages.error(self.request, 'Home Assistant not responding, {}'.format(e), fail_silently=True)
    #     return super().form_invalid(form)


class ConfigurationMasterSlaveViewOld(FormView):
    template_name = 'wiringcentralconfigurator_app/wc_master_slave_configurator.html'
    form_class = ConfigurationMasterSlaveForm
    success_url = reverse_lazy('list_board_view')

    def get_kwargs(self):
        kwargs = self.kwargs.get('board')
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        board_name = self.kwargs.get('board')
        board_choices = [("NO FOLLOW", "NO FOLLOW")]
        for num in range(1, 9):
            board_choices.append(("{}-{}".format(board_name, num), "{}-{}".format(board_name, num)))
        kwargs["board_choices"] = board_choices
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        board_name = self.kwargs.get('board')
        for num in range(1, 9):
            initial["name_{}".format(num)] = "{}-{}".format(board_name, num)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        token_obj = LongLivedAccessToken.objects.first()
        board_name = self.kwargs.get('board')
        context['entity_name'] = board_name
        context['thermostatID'] = board_name

        # print(board_choices)
        # context['form'] = self.form_class(
        #     initial={"name_{}".format(num): "{}-{}".format(board_name, num) for num in range(0, 9)},
        #     board_choices=board_choices)
        if self.kwargs.get('board') is not None:
            if token_obj is not None and board_name is not None:
                try:
                    # Read the current masterslave config
                    status, board_data = get_board_masterslave_configuration(token_obj.token, board_name)
                    print("status, board_data", status, board_data)
                    # status = True
                    # board_data = [{'name': 'WC-12345678-1', 'master': 'WC-12345678-1'}, {'name': 'WC-12345678-2', 'master': 'WC-12345678-2'}, {'name': 'WC-12345678-3', 'master': 'WC-12345678-3'}, {'name': 'WC-12345678-4', 'master': 'WC-12345678-4'}, {'name': 'WC-12345678-5', 'master': 'WC-12345678-5'}, {'name': 'WC-12345678-6', 'master': 'WC-12345678-6'}, {'name': 'WC-12345678-7', 'master': 'WC-12345678-7'}, {'name': 'WC-12345678-8', 'master': 'WC-12345678-8'}]

                    if status:
                        # try:
                        #     board_data = json.loads(board_data)
                        # except Exception as e:
                        #     print("Exception {}".format(e))
                        #     messages.info(self.request, 'No previous configuration found.', fail_silently=True)
                        #     return context
                        initial = {}
                        if len(board_data) == 0:
                            messages.info(self.request, 'No masterslave configuration found.', fail_silently=True)
                            context['thermostatID'] = board_name
                            return context

                        num = 1
                        for data in board_data:
                            initial['name_{}'.format(num)] = data['name']
                            initial['type_{}'.format(num)] = data['master']
                            num += 1
                        print(initial)
                        board_choices = [("NO FOLLOW", "NO FOLLOW")]
                        for num in range(1, 9):
                            board_choices.append(("{}-{}".format(board_name, num), "{}-{}".format(board_name, num)))
                        context['form'] = self.form_class(initial=initial, board_choices=board_choices)
                    # board_obj = get_board_details(token_obj.token, self.get_kwargs())
                    # if board_obj[0]:
                    #     # print(board_obj)
                    #     context['thermostatID'] = board_name
                    else:
                        messages.error(self.request, 'Cannot get masterslave configuration', fail_silently=True)
                except Exception as e:
                    print("Exception, {}".format(e))
                    messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return context

    def form_invalid(self, form):
        print("form invalid")
        print(form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        datas = []
        board_name = self.kwargs.get('board')
        if self.request.method == "POST":
            board_choices = [("NO FOLLOW", "NO FOLLOW")]
            for num in range(0, 9):
                board_choices.append(("{}-{}".format(board_name, num), "{}-{}".format(board_name, num)))
            # form = self.form_class(self.request.POST, board_choices=board_choices)
            if form.is_valid():
                for num in range(1, 9):
                    datas.append({"name": form.cleaned_data['name_{}'.format(num)],
                                  "master": form.cleaned_data['type_{}'.format(num)]})
                print("=======")
                print(datas)
                token_obj = LongLivedAccessToken.objects.first()
                if token_obj is not None and self.get_kwargs() is not None:
                    pass
                    try:
                        # Post the new master slave config
                        status, message = post_board_masterslave_configuration(token_obj.token, board_id=board_name, data=datas)
                        if not status:
                            messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
                            return HttpResponseRedirect(reverse_lazy('configuration_masterslave_view', kwargs={"board": board_name}))
                        messages.success(self.request, 'Master/Slave Configuration applied successfully!', fail_silently=True)
                        return HttpResponseRedirect(self.success_url)
                    except Exception as e:
                        print("Exception: {}".format(e))
                        messages.error(self.request, 'Home Assistant not responding, {}'.format(e), fail_silently=True)
        return super().form_invalid(form)


class ConfigurationDefaultRulesView(FormView):
    template_name = 'wiringcentralconfigurator_app/wc_default_rule_configurator.html'
    form_class = ConfigurationDefaultRuleFormSet
    # success_url = reverse_lazy('list_board_view')

    def get_success_url(self):
        return reverse('configuration_default_rules_view', kwargs={'board': self.kwargs.get('board')})

    def get_kwargs(self):
        kwargs = self.kwargs.get('board')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        token_obj = LongLivedAccessToken.objects.first()
        board_name = self.kwargs.get('board')
        context['entity_name'] = board_name
        context['thermostatID'] = board_name

        # print(context['form'])
        def get_time(time_data: str):
            t_data = datetime.datetime.now().time()
            t_data = t_data.replace(hour=int(time_data.split(":")[0]), minute=int(time_data.split(":")[1]))
            return t_data

        if self.kwargs.get('board') is not None:
            if token_obj is not None and board_name is not None:
                try:
                    # Read the current defaultrule config
                    status, board_data = get_board_defaultrule_configuration(token_obj.token, board_name)
                    print("status, board_data", status, board_data)
                    # status = True
                    # board_data = [{'name': 'WC-12345678-1', 'master': 'WC-12345678-1'}, {'name': 'WC-12345678-2', 'master': 'WC-12345678-2'}, {'name': 'WC-12345678-3', 'master': 'WC-12345678-3'}, {'name': 'WC-12345678-4', 'master': 'WC-12345678-4'}, {'name': 'WC-12345678-5', 'master': 'WC-12345678-5'}, {'name': 'WC-12345678-6', 'master': 'WC-12345678-6'}, {'name': 'WC-12345678-7', 'master': 'WC-12345678-7'}, {'name': 'WC-12345678-8', 'master': 'WC-12345678-8'}]

                    if status:
                        # data = {'form-TOTAL_FORMS': 10, 'form-INITIAL_FORMS': f'{len(board_data)}'}
                        initial = []
                        for init_data in board_data:
                            initial.append({
                                'starttime': get_time(init_data['starttime_default']),
                                'endtime': get_time(init_data['endtime_default']),
                                'target_temperature': init_data['target_temperature_default'],
                                'day_of_week': init_data['day_of_week_default'],
                                'hvac_mode': init_data['hvac_mode_default'],
                                            })
                        context['form'] = self.form_class(initial=initial)
                    else:
                        messages.error(self.request, 'Cannot get defaultrule configuration', fail_silently=True)
                except Exception as e:
                    print("Exception, {}".format(e))
                    messages.error(self.request, 'Home Assistant not responding', fail_silently=True)
        return context

    def form_invalid(self, form):
        print("form invalid")
        messages.error(self.request, 'Error occured: {}'.format(form.errors), fail_silently=True)
        return super().form_invalid(form)

    def form_valid(self, form):
        datas = []
        board_name = self.kwargs.get('board')

        def get_time_str(time_data: datetime.time):
            return f"{time_data.hour}:{time_data.minute}"

        if self.request.method == "POST":
            if form.is_valid():
                for iform in form:
                    print(iform.cleaned_data)
                    if iform.cleaned_data['DELETE']:
                        continue
                    datas.append({
                        'ruleid_default': "WiringCentral:Default_Cloned:{}:{}".format(random.randint(0, 1000),
                                                                     int(time.time())),
                        'starttime_default': get_time_str(iform.cleaned_data['starttime']),
                        'endtime_default': get_time_str(iform.cleaned_data['endtime']),
                        'target_temperature_default': iform.cleaned_data['target_temperature'],
                        'day_of_week_default': iform.cleaned_data['day_of_week'],
                        'hvac_mode_default': iform.cleaned_data['hvac_mode'],
                    })
                token_obj = LongLivedAccessToken.objects.first()
                if token_obj is not None and self.get_kwargs() is not None:
                    pass
                    try:
                        # Post the new default rule config
                        status, message = post_board_default_rule_configuration(token_obj.token, board_id=board_name, data=datas)
                        if not status:
                            messages.error(self.request, 'Error occured: {}'.format(message), fail_silently=True)
                            return HttpResponseRedirect(reverse_lazy('configuration_default_rules_view', kwargs={"board": board_name}))
                        messages.success(self.request, 'DefaultRule Configuration saved successfully!', fail_silently=True)
                        # return HttpResponseRedirect(self.success_url)
                        return HttpResponseRedirect(self.get_success_url())
                    except Exception as e:
                        print("Exception: {}".format(e))
                        messages.error(self.request, 'Home Assistant not responding, {}'.format(e), fail_silently=True)
        return super().form_invalid(form)